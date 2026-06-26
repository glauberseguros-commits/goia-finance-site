"""
Pipeline documental da GOIA.

Responsável por organizar o fluxo:
upload -> extração -> classificação -> validação -> gravação -> financeiro.
"""

from datetime import datetime


def criar_contexto_documento(nome_arquivo="", tipo="", origem="upload", empresa_id=None):
    return {
        "empresa_id": empresa_id,
        "nome_arquivo": nome_arquivo,
        "tipo": tipo,
        "origem": origem,
        "status": "Recebido",
        "criado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "texto_extraido": "",
        "dados_extraidos": {},
        "erros": [],
        "alertas": [],
    }


def classificar_documento(nome_arquivo, texto=""):
    nome = str(nome_arquivo or "").lower()
    conteudo = str(texto or "").lower()

    if nome.endswith(".ofx") or "ofx" in nome:
        return "OFX"

    if "nfe" in nome or "nf-e" in conteudo or "nota fiscal eletrônica" in conteudo:
        return "NF-e"

    if "boleto" in nome or "linha digitável" in conteudo:
        return "Boleto"

    if "pix" in nome or "comprovante pix" in conteudo:
        return "PIX"

    if "contrato" in nome:
        return "Contrato"

    return "Documento"


def validar_contexto_documento(ctx):
    erros = []

    if not ctx.get("empresa_id"):
        erros.append("Empresa não informada.")

    if not ctx.get("nome_arquivo"):
        erros.append("Nome do arquivo não informado.")

    ctx["erros"] = erros
    ctx["status"] = "Com erro" if erros else "Validado"

    return ctx
