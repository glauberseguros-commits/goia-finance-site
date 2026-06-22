from pathlib import Path

p = Path("pages/1_Importar_Documento.py")
txt = p.read_text(encoding="utf-8")

alvo = '''        if emitente_doc == DOC_EMPRESA_LOGADA:
            direcao = "Nota Fiscal de Venda"
            parte_doc = destinatario_doc
            parte_nome = destinatario_nome

        elif destinatario_doc == DOC_EMPRESA_LOGADA:
            direcao = "Nota Fiscal de Compra"
            parte_doc = emitente_doc
            parte_nome = emitente_nome

        else:
            direcao = "Nota Fiscal - Conferência necessária"
            parte_doc = destinatario_doc or emitente_doc
            parte_nome = destinatario_nome or emitente_nome
'''

novo = '''        if emitente_doc == DOC_EMPRESA_LOGADA and destinatario_doc and destinatario_nome:
            direcao = "Nota Fiscal de Venda"
            parte_doc = destinatario_doc
            parte_nome = destinatario_nome

        elif destinatario_doc == DOC_EMPRESA_LOGADA and emitente_doc and emitente_nome:
            direcao = "Nota Fiscal de Compra"
            parte_doc = emitente_doc
            parte_nome = emitente_nome

        else:
            direcao = "Nota Fiscal - Conferência necessária"
            parte_doc = destinatario_doc or emitente_doc
            parte_nome = destinatario_nome or emitente_nome
'''

if alvo not in txt:
    raise SystemExit("Bloco de decisão NF-e não encontrado. Não alterei nada.")

txt = txt.replace(alvo, novo)

p.write_text(txt, encoding="utf-8")

print("Regra de segurança aplicada: NF-e sem contraparte vai para conferência.")
