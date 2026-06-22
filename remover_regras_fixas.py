from pathlib import Path

p = Path("pages/1_Importar_Documento.py")
txt = p.read_text(encoding="utf-8")

substituicoes = [

(
'''def sugerir_direcao_nf(texto):
    t = (texto or "").upper()

    if "COMANDO DA MARINHA" in t:
        return "Nota Fiscal de Venda"

    if "DESTINATÁRIO" in t and CNPJ_EMPRESA in texto:
        return "Nota Fiscal de Compra"

    return "Nota Fiscal de Compra"
''',
'''def sugerir_direcao_nf(texto):
    return "Nota Fiscal - Conferência necessária"
'''
),

(
'''    # Emitente conhecido: própria empresa GODS.
    if (
        "GODS PRODUTOS" in t_up
        or "GO LICITAÇÕES" in t_up
        or "GO LICITACOES" in t_up
        or CNPJ_EMPRESA in cnpjs
    ):
        emitente_nome = "GODS PRODUTOS SERVICOS & EVENTOS LTDA"
        emitente_cnpj = CNPJ_EMPRESA
''',
'''    if CNPJ_EMPRESA in cnpjs:
        emitente_cnpj = CNPJ_EMPRESA
'''
),

(
'''    # Emitente conhecido: fornecedor Ponto Certo.
    if "PONTO CERTO" in t_up:
        emitente_nome = "PONTO CERTO COMERCIO DE FERRAGENS LTDA"
        emitente_cnpj = "11.877.694/0001-66"
''',
''
),

(
'''    # Destinatário conhecido: Marinha.
    if "COMANDO DA MARINHA" in t_up:
        destinatario_nome = "COMANDO DA MARINHA"
        for c in cnpjs:
            if c != CNPJ_EMPRESA:
                destinatario_cnpj = c
                break
''',
''
),

(
'''            if "COMANDO DA MARINHA" in trecho_up:
                destinatario_nome = "COMANDO DA MARINHA"
''',
''
),

(
'''        nome_orgao = "Órgão Público"

        texto_up = (texto or "").upper()

        if "ESTADO-MAIOR DA ARMADA" in texto_up:
            nome_orgao = "ESTADO-MAIOR DA ARMADA"

        elif "COMANDO DA MARINHA" in texto_up:
            nome_orgao = "COMANDO DA MARINHA"
''',
'''        nome_orgao = "Órgão Público"
'''
)

]

for antigo, novo in substituicoes:
    txt = txt.replace(antigo, novo)

p.write_text(txt, encoding="utf-8")

print("Regras fixas removidas.")
