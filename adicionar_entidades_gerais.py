from pathlib import Path

p = Path("pages/1_Importar_Documento.py")
txt = p.read_text(encoding="utf-8")

# 1) Inserir função de extração geral antes de analisar_documento
marcador = "def analisar_documento(texto):"

nova_funcao = r'''
def extrair_entidades_documento(texto):
    texto = texto or ""
    linhas = [x.strip() for x in texto.splitlines() if x.strip()]

    documentos = encontrar_documentos(texto)

    emails = re.findall(
        r"[\w\.-]+@[\w\.-]+\.\w+",
        texto,
        flags=re.I
    )
    emails = list(dict.fromkeys([e.strip().lower() for e in emails]))

    telefones_raw = re.findall(
        r"(?:\(?\d{2}\)?\s*)?(?:9\s*)?\d{4}[-\s]?\d{4}",
        texto
    )

    telefones = []
    for tel in telefones_raw:
        nums = re.sub(r"\D", "", tel)
        if 8 <= len(nums) <= 11:
            telefones.append(nums)

    telefones = list(dict.fromkeys(telefones))

    nomes = []

    padroes_nome = [
        r"NOME EMPRESARIAL\s+(.+)",
        r"NOME / RAZÃO SOCIAL\s+(.+)",
        r"NOME / RAZAO SOCIAL\s+(.+)",
        r"RAZÃO SOCIAL\s+(.+)",
        r"RAZAO SOCIAL\s+(.+)",
        r"NOME FANTASIA\s+(.+)",
        r"FANTASIA\s+(.+)",
    ]

    for padrao in padroes_nome:
        for m in re.finditer(padrao, texto, flags=re.I):
            nome = " ".join((m.group(1) or "").split())
            if nome:
                nomes.append(nome[:140])

    palavras_ruido = [
        "DANFE", "DOCUMENTO AUXILIAR", "CHAVE DE ACESSO",
        "PROTOCOLO", "CONSULTA", "AUTENTICIDADE",
        "NATUREZA DA OPERAÇÃO", "NATUREZA DA OPERACAO",
        "CNPJ", "CPF", "INSCRIÇÃO", "INSCRICAO",
        "ENDEREÇO", "ENDERECO", "BAIRRO", "CEP",
        "MUNICÍPIO", "MUNICIPIO", "UF", "FONE", "FAX",
        "DATA", "HORA", "VALOR", "TOTAL", "PRODUTO",
        "CÁLCULO", "CALCULO", "IMPOSTO", "TRANSPORTADOR"
    ]

    for i, linha in enumerate(linhas):
        up = linha.upper()

        if any(r in up for r in palavras_ruido):
            continue

        if re.search(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}", linha):
            continue

        if re.search(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}", linha):
            continue

        if len(re.sub(r"\D", "", linha)) >= 8:
            continue

        if len(linha) >= 5 and any(c.isalpha() for c in linha):
            nomes.append(" ".join(linha.split())[:140])

    nomes = list(dict.fromkeys(nomes))

    cidades_ufs = []
    ufs = "AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO"

    for linha in linhas:
        m = re.search(rf"\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ\s]+)\s+({ufs})\b", linha.upper())
        if m:
            cidade = " ".join(m.group(1).split()).title()
            uf = m.group(2)
            cidades_ufs.append({"cidade": cidade, "uf": uf})

    return {
        "documentos": documentos,
        "emails": emails,
        "telefones": telefones,
        "nomes_possiveis": nomes[:10],
        "cidades_ufs": cidades_ufs[:10],
    }


'''

if "def extrair_entidades_documento(texto):" not in txt:
    txt = txt.replace(marcador, nova_funcao + "\n" + marcador)

# 2) Adicionar entidades no retorno do analisar_documento
alvo = '''def analisar_documento(texto):
    tipo = classificar_tipo_documento(texto)
    documentos = encontrar_documentos(texto)
    datas = encontrar_datas(texto)
'''

novo = '''def analisar_documento(texto):
    tipo = classificar_tipo_documento(texto)
    documentos = encontrar_documentos(texto)
    entidades = extrair_entidades_documento(texto)
    datas = encontrar_datas(texto)
'''

if alvo not in txt:
    raise SystemExit("Cabeçalho de analisar_documento não encontrado.")

txt = txt.replace(alvo, novo)

alvo_retorno = '''        "documentos_encontrados": documentos,
        "parte_cnpj": parte_doc,
'''

novo_retorno = '''        "documentos_encontrados": documentos,
        "entidades_extraidas": entidades,
        "parte_cnpj": parte_doc,
'''

if alvo_retorno not in txt:
    raise SystemExit("Retorno de analisar_documento não encontrado.")

txt = txt.replace(alvo_retorno, novo_retorno)

# 3) Mostrar entidades no card da interface
alvo_ui = '''                with st.expander("Diagnóstico técnico"):
                    st.json(analise)
'''

novo_ui = '''                with st.expander("Diagnóstico técnico"):
                    st.json(analise)

                entidades = analise.get("entidades_extraidas", {})

                if entidades:
                    with st.expander("Entidades encontradas no documento"):
                        st.write("**Documentos encontrados:**", entidades.get("documentos", []))
                        st.write("**E-mails encontrados:**", entidades.get("emails", []))
                        st.write("**Telefones encontrados:**", entidades.get("telefones", []))
                        st.write("**Nomes possíveis:**", entidades.get("nomes_possiveis", []))
                        st.write("**Cidades/UF possíveis:**", entidades.get("cidades_ufs", []))
'''

if alvo_ui not in txt:
    raise SystemExit("Bloco de diagnóstico técnico na interface não encontrado.")

txt = txt.replace(alvo_ui, novo_ui)

p.write_text(txt, encoding="utf-8")

print("Camada de extração geral de entidades adicionada.")
