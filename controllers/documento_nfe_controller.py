from utils.services.documento.nfe_xml_service import ler_nfe_xml, ler_nfe_xml_dto


class DocumentoNFeController:

    @staticmethod
    def ler(xml_bytes):
        return ler_nfe_xml(xml_bytes)

    @staticmethod
    def ler_dto(xml_bytes):
        return ler_nfe_xml_dto(xml_bytes)
