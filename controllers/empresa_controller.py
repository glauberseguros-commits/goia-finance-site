from utils.services.empresa_service import listar_assinantes

class EmpresaController:

    @staticmethod
    def listar():
        return listar_assinantes()
