from utils.services.documento.texto_service import (
    remover_acentos,
    somente_numeros,
    normalizar_linha_ocr,
    normalizar_texto_ocr,
    texto_para_busca,
    formatar_documento,
)


class DocumentoTextoController:

    @staticmethod
    def remover_acentos(valor):
        return remover_acentos(valor)

    @staticmethod
    def somente_numeros(valor):
        return somente_numeros(valor)

    @staticmethod
    def normalizar_linha(linha):
        return normalizar_linha_ocr(linha)

    @staticmethod
    def normalizar_texto(texto):
        return normalizar_texto_ocr(texto)

    @staticmethod
    def texto_busca(texto):
        return texto_para_busca(texto)

    @staticmethod
    def formatar_documento(valor):
        return formatar_documento(valor)
