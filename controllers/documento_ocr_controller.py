from utils.services.documento.ocr_service import (
    extrair_texto_pypdf,
    extrair_texto_ocr,
    extrair_texto_pdf,
)


class DocumentoOCRController:

    @staticmethod
    def extrair_pdf(arquivo):
        return extrair_texto_pdf(arquivo)

    @staticmethod
    def extrair_pypdf(arquivo):
        return extrair_texto_pypdf(arquivo)

    @staticmethod
    def extrair_ocr(arquivo):
        return extrair_texto_ocr(arquivo)
