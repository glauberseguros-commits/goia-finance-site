from utils.services.documento_pipeline_service import (
    criar_contexto_documento,
    classificar_documento,
    validar_contexto_documento,
)


class DocumentoPipelineController:

    @staticmethod
    def criar_contexto(nome_arquivo="", tipo="", origem="upload", empresa_id=None):
        return criar_contexto_documento(nome_arquivo, tipo, origem, empresa_id)

    @staticmethod
    def classificar(nome_arquivo, texto=""):
        return classificar_documento(nome_arquivo, texto)

    @staticmethod
    def validar(ctx):
        return validar_contexto_documento(ctx)
