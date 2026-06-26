from utils.services.admin_service import (
    listar_auditoria_admin,
)

class AdminAuditoriaController:

    @staticmethod
    def listar(limite=100):
        return listar_auditoria_admin(limite)
