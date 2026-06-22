from pathlib import Path
import re

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
        descricao = extrair_tag_ofx(bloco, "MEMO") or extrair_tag_ofx(bloco, "NAME") or "Movimento OFX"
        documento = extrair_tag_ofx(bloco, "FITID")
        tipo = "Credito" if valor > 0 else "Debito"

        cur.execute("""
            SELECT id FROM movimentos_bancarios
            WHERE empresa_id = ?
              AND IFNULL(documento, '') = IFNULL(?, '')
              AND IFNULL(data_movimento, '') = IFNULL(?, '')
              AND IFNULL(valor, 0) = IFNULL(?, 0)
              AND IFNULL(origem, '') = IFNULL(?, '')
        """, (EMPRESA_ID_ATIVA, documento, data_movimento, valor, nome_arquivo))

        if cur.fetchone():
            ignorados += 1
            continue

        cur.execute("""
            INSERT INTO movimentos_bancarios (
                empresa_id, data_movimento, descricao, documento,
                valor, tipo, conciliado, origem
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            EMPRESA_ID_ATIVA, data_movimento, descricao[:250],
            documento, valor, tipo, 0, nome_arquivo
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

txt = re.sub(
    r'"Anexar documentos PDF"\s*,\s*\n\s*type=\["pdf"\]\s*,',
    '"Anexar documentos PDF, OFX, CSV ou TXT",\n    type=["pdf", "ofx", "csv", "txt"],',
    txt
)

pattern = r'(?m)^(\s*)texto\s*=\s*extrair_texto_pdf\(arquivo\)\s*\n\1analise\s*=\s*analisar_documento\(texto\)\s*\n\1resultado\s*=\s*salvar_documento_erp\(arquivo\.name,\s*texto,\s*analise\)\s*'

replacement = r'''\1extensao = arquivo.name.lower().split(".")[-1]

\1if extensao == "pdf":
\1    texto = extrair_texto_pdf(arquivo)
\1    analise = analisar_documento(texto)
\1    resultado = salvar_documento_erp(arquivo.name, texto, analise)

\1elif extensao == "ofx":
\1    conteudo = arquivo.getvalue()
\1    try:
\1        texto = conteudo.decode("utf-8")
\1    except Exception:
\1        try:
\1            texto = conteudo.decode("latin-1")
\1        except Exception:
\1            texto = ""

\1    resultado_ofx = processar_ofx_bancario(arquivo.name, texto)

\1    with st.container(border=True):
\1        st.markdown(f"### 🏦 {arquivo.name}")
\1        st.success(
\1            f"OFX processado. Movimentos inseridos: {resultado_ofx['movimentos_inseridos']} | "
\1            f"Ignorados/duplicados: {resultado_ofx['movimentos_ignorados']}"
\1        )
\1        st.json(resultado_ofx)

\1    continue

\1elif extensao in ["csv", "txt"]:
\1    with st.container(border=True):
\1        st.markdown(f"### 📄 {arquivo.name}")
\1        st.warning(f"Arquivo {extensao.upper()} aceito. Processador específico ainda será implementado.")
\1    continue

\1else:
\1    st.warning(f"Formato não suportado: {arquivo.name}")
\1    continue
'''

txt2, n = re.subn(pattern, replacement, txt)

if n == 0:
    raise SystemExit("Não encontrei as 3 linhas de processamento PDF para substituir.")

p.write_text(txt2, encoding="utf-8")
print("Importador atualizado com OFX. Substituições:", n)
