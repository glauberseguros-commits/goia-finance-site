from pathlib import Path

p = Path("pages/1_Importar_Documento.py")
txt = p.read_text(encoding="utf-8")

def trocar_funcao(txt, nome, novo):
    inicio = txt.index(f"def {nome}(")
    prox = txt.find("\ndef ", inicio + 1)
    if prox == -1:
        prox = len(txt)
    return txt[:inicio] + novo.rstrip() + "\n\n" + txt[prox:].lstrip("\n")

nova_extrair_nome = r'''def extrair_nome_do_bloco(bloco):
    linhas = [x.strip() for x in (bloco or "").splitlines() if x.strip()]

    ignorar = [
        "DANFE", "DOCUMENTO AUXILIAR", "NF-E", "NFE",
        "DESTINATÁRIO", "DESTINATARIO", "REMETENTE", "EMITENTE",
        "NOME / RAZÃO SOCIAL", "NOME / RAZAO SOCIAL",
        "CNPJ", "CPF", "ENDEREÇO", "ENDERECO", "BAIRRO", "CEP",
        "MUNICÍPIO", "MUNICIPIO", "UF", "FONE", "FAX",
        "INSCRIÇÃO ESTADUAL", "INSCRICAO ESTADUAL",
        "DATA DA EMISSÃO", "DATA DA EMISSAO", "DATA DA SAÍDA", "DATA DA SAIDA",
        "CHAVE DE ACESSO", "PROTOCOLO", "AUTORIZAÇÃO", "AUTORIZACAO",
        "CONSULTA DE AUTENTICIDADE", "WWW.NFE", "WWW.FAZENDA",
        "NATUREZA DA OPERAÇÃO", "NATUREZA DA OPERACAO",
        "SÉRIE", "SERIE", "FOLHA", "SAÍDA", "SAIDA", "ENTRADA"
    ]

    def linha_valida(linha):
        up = linha.upper()

        if len(linha.strip()) < 5:
            return False

        if any(x in up for x in ignorar):
            return False

        if re.search(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}", linha):
            return False

        if re.search(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}", linha):
            return False

        if len(re.sub(r"\D", "", linha)) >= 8:
            return False

        return True

    # 1) Preferência: linha após NOME / RAZÃO SOCIAL.
    for i, linha in enumerate(linhas):
        up = linha.upper()

        if "NOME / RAZÃO SOCIAL" in up or "NOME / RAZAO SOCIAL" in up:
            for prox in linhas[i + 1:i + 6]:
                if linha_valida(prox):
                    return " ".join(prox.split())[:140]

    # 2) Fallback: primeira linha textual válida do bloco.
    for linha in linhas:
        if linha_valida(linha):
            return " ".join(linha.split())[:140]

    return ""'''

nova_emitente = r'''def extrair_bloco_emitente_nfe(texto):
    linhas = [x.rstrip() for x in (texto or "").splitlines()]

    idx_dest = None
    for i, linha in enumerate(linhas):
        up = linha.upper()
        if "DESTINATÁRIO" in up or "DESTINATARIO" in up or "REMETENTE" in up:
            idx_dest = i
            break

    trecho = "\n".join(linhas[:idx_dest]) if idx_dest is not None else "\n".join(linhas)

    # Se existir uma linha com CNPJ antes do destinatário, usa uma janela ao redor dela.
    docs = encontrar_documentos(trecho)
    if DOC_EMPRESA_LOGADA in docs:
        doc_ref = DOC_EMPRESA_LOGADA
    else:
        doc_ref = docs[0] if docs else ""

    if doc_ref:
        doc_limpo = somente_numeros(doc_ref)
        for i, linha in enumerate(trecho.splitlines()):
            if doc_limpo in somente_numeros(linha):
                ini = max(0, i - 6)
                fim = min(len(trecho.splitlines()), i + 8)
                return "\n".join(trecho.splitlines()[ini:fim])

    return trecho'''

nova_destinatario = r'''def extrair_bloco_destinatario_nfe(texto):
    bloco = cortar_bloco(
        texto,
        ["DESTINATÁRIO", "DESTINATARIO", "REMETENTE"],
        [
            "PAGAMENTOS",
            "CÁLCULO DO IMPOSTO",
            "CALCULO DO IMPOSTO",
            "TRANSPORTADOR",
            "DADOS DOS PRODUTOS",
            "DADOS ADICIONAIS",
            "FATURA",
            "DUPLICATA"
        ]
    )

    if bloco:
        return bloco

    # Fallback conservador: se não achou cabeçalho, não inventa destinatário.
    return ""'''

txt = trocar_funcao(txt, "extrair_nome_do_bloco", nova_extrair_nome)
txt = trocar_funcao(txt, "extrair_bloco_emitente_nfe", nova_emitente)
txt = trocar_funcao(txt, "extrair_bloco_destinatario_nfe", nova_destinatario)

p.write_text(txt, encoding="utf-8")

print("Extração por blocos ajustada.")
