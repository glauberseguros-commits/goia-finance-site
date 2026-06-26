from utils.services.admin_service import (
    obter_metricas_admin,
    listar_assinantes_admin,
    buscar_assinante_admin,
    alterar_status_assinante,
    alterar_plano_assinante,
    excluir_assinante_admin,
    listar_auditoria_admin,
)

class AdminController:

    @staticmethod
    def metricas():
        return obter_metricas_admin()

    @staticmethod
    def assinantes():
        return listar_assinantes_admin()

    @staticmethod
    def buscar(empresa_id):
        return buscar_assinante_admin(empresa_id)

    @staticmethod
    def alterar_status(empresa_id, status, motivo=""):
        alterar_status_assinante(empresa_id, status, motivo)

    @staticmethod
    def alterar_plano(empresa_id, plano, data_inicio=None, data_fim=None):
        alterar_plano_assinante(
            empresa_id,
            plano,
            data_inicio,
            data_fim,
        )

    @staticmethod
    def excluir(empresa_id):
        excluir_assinante_admin(empresa_id)

    @staticmethod
    def auditoria(limite=100):
        return listar_auditoria_admin(limite)
