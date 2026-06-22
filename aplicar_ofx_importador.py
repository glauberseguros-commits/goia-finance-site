from pathlib import Path

p = Path("pages/1_Importar_Documento.py")
txt = p.read_text(encoding="utf-8")

func = r'''

def garantir_estrutura_movimentos_bancarios():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS movimentos_bancarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            data_movimento TEXT,
            descricao TEXT,
            documento TEXT,
            valor REAL,
            tipo TEXT,
            conciliado INTEGER DEFAULT 0,
            origem TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def extrair_tag_ofx(bloco, tag):
    m = re.search(rf"<{tag}>(.*?)(?:\n|<)", bloco or "", flags=re.I | re.S)
    return m.group(1).strip() if m else ""


def converter_data_ofx(valor):
    nums = somente_numeros(valor)
    if len(nums) >= 8:
        return f"{nums[:4]}-{nums[4:6]}-{nums[6:8]}"
    return None


def converter_valor_ofx(valor):
    try:
        return float(str(valor or "0").replace(",", ".").strip())
    except Exception:
        return 0.0


def processar_ofx_bancario(nome_arquivo, texto):
    garantir_estrutura_movimentos_bancarios()

    blocos = re.findall(
        r"<STMTTRN>(.*?)(?=<STMTTRN>|</BANKTRANLIST>|</OFX>)",
        texto or "",
        flags=re.I | re.S
    )

    conn = conectar()
    cur = conn.cursor()

    inseridos = 0
    ignorados = 0

    for bloco in blocos:
        data_movimento = converter_data_ofx(extrair_tag_ofx(bloco, "DTPOSTED"))
        valor = converter_valor_ofx(extrair_tag_ofx(bloco, "TRNAMT"))
        descricao = (
            extrair_tag_ofx(bloco, "MEMO")
            or extrair_tag_ofx(bloco, "NAME")
            or "Movimento OFX"
        )
        documento = extrair_tag_ofx(bloco, "FITID")
        tipo = "Credito" if valor > 0 else "Debito"

        cur.execute("""
            SELECT id
            FROM movimentos_bancarios
            WHERE empresa_id = ?
              AND IFNULL(documento, '') = IFNULL(?, '')
              AND IFNULL(data_movimento, '') = IFNULL(?, '')
              AND IFNULL(valor, 0) = IFNULL(?, 0)
              AND IFNULL(origem, '') = IFNULL(?, '')
        """, (
            EMPRESA_ID_ATIVA,
            documento,
            data_movimento,
            valor,
            nome_arquivo
        ))

        if cur.fetchone():
            ignorados += 1
            continue

        cur.execute("""
            INSERT INTO movimentos_bancarios (
                empresa_id,
                data_movimento,
                descricao,
                documento,
                valor,
                tipo,
                conciliado,
                origem
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            EMPRESA_ID_ATIVA,
            data_movimento,
            descricao[:250],
            documento,
            valor,
            tipo,
            0,
            nome_arquivo
        ))

        inseridos += 1

    conn.commit()
    conn.close()

    return {
        "tipo_detectado": "Extrato Bancário",
        "direcao_sugerida": "OFX - Movimentos bancários importados",
        "total_movimentos": len(blocos),
        "movimentos_inseridos": inseridos,
        "movimentos_ignorados": ignorados,
    }
'''

if "def processar_ofx_bancario(" not in txt:
    txt = txt.replace("# =========================\n# BANCO\n# =========================", func + "\n\n# =========================\n# BANCO\n# =========================")

txt = txt.replace(
    '"Anexar documentos PDF",\n    type=["pdf"],',
    '"Anexar documentos PDF, OFX, CSV ou TXT",\n    type=["pdf", "ofx", "csv", "txt"],'
)

antigo = '''    for arquivo in arquivos:
        try:
            texto = extrair_texto_pdf(arquivo)
            analise = analisar_documento(texto)
            resultado = salvar_documento_erp(arquivo.name, texto, analise)
'''

novo = '''    for arquivo in arquivos:
        try:
            extensao = arquivo.name.lower().split(".")[-1]

            if extensao == "pdf":
                texto = extrair_texto_pdf(arquivo)
                analise = analisar_documento(texto)
                resultado = salvar_documento_erp(arquivo.name, texto, analise)

            elif extensao == "ofx":
                conteudo = arquivo.getvalue()
                try:
                    texto = conteudo.decode("utf-8")
                except Exception:
                    try:
                        texto = conteudo.decode("latin-1")
                    except Exception:
                        texto = ""

                resultado_ofx = processar_ofx_bancario(arquivo.name, texto)

                with st.container(border=True):
                    st.markdown(f"### 🏦 {arquivo.name}")
                    st.success(
                        f"OFX processado. Movimentos inseridos: {resultado_ofx['movimentos_inseridos']} | "
                        f"Ignorados/duplicados: {resultado_ofx['movimentos_ignorados']}"
                    )
                    st.json(resultado_ofx)

                continue

            elif extensao in ["csv", "txt"]:
                with st.container(border=True):
                    st.markdown(f"### 📄 {arquivo.name}")
                    st.warning(f"Arquivo {extensao.upper()} aceito. Processador específico ainda será implementado.")
                continue

            else:
                st.warning(f"Formato não suportado: {arquivo.name}")
                continue
'''

if antigo not in txt:
    raise SystemExit("Bloco principal de processamento não encontrado.")

txt = txt.replace(antigo, novo)

p.write_text(txt, encoding="utf-8")
print("Importador atualizado com suporte inicial a OFX.")
