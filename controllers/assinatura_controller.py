from utils.services.assinatura_service import status_assinatura_valido

class AssinaturaController:

    @staticmethod
    def validar(status):
        return status_assinatura_valido(status)
