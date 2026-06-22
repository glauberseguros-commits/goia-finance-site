from pathlib import Path

p = Path("pages/1_Importar_Documento.py")
txt = p.read_text(encoding="utf-8")

if "def extrair_entidades_documento(texto):" not in txt:
    marcador = "\ndef analisar_documento(texto):"

    func = r'''

def extrair_entidades_documento(texto):
    texto = texto or ""
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
        nums = somente_numeros(tel)
        if 8 <= len(nums) <= 11:
            telefones.append(nums)

    nomes = []
    linhas = [x.strip() for x in texto.splitlines() if x.strip()]

    for doc in documentos:
        nome = identificar_nome_por_documento(texto, doc)
        if nome:
            nomes.append(nome)

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

    for linha in linhas:
        up = linha.upper()

        if any(r in up for r in palavras_ruido):
            continue

        if len(somente_numeros(linha)) >= 8:
            continue

        if len(linha) >= 5 and any(c.isalpha() for c in linha):
            nomes.append(" ".join(linha.split())[:140])

    return {
        "documentos": documentos,
        "emails": emails,
        "telefones": list(dict.fromkeys(telefones)),
        "nomes_possiveis": list(dict.fromkeys(nomes))[:10],
    }
'''

    txt = txt.replace(marcador, func + marcador)
    p.write_text(txt, encoding="utf-8")
    print("Função extrair_entidades_documento recriada.")
else:
    print("Função extrair_entidades_documento já existe.")
