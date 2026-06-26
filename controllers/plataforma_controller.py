from utils.services.plataforma_service import obter_status_plataforma

class PlataformaController:

    @staticmethod
    def status():
        return obter_status_plataforma()
