from utils.services.documento.nfe_xml_service import ler_nfe_xml


class DocumentoNFeController:

    @staticmethod
    def ler(xml_bytes):
        return ler_nfe_xml(xml_bytes)
