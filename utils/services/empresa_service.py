from utils.repositories.empresas import (
    listar_empresas,
    buscar_empresa_por_id,
    buscar_empresa_por_cnpj,
    atualizar_status_empresa,
    cancelar_empresa,
)

def listar_assinantes():
    return listar_empresas()
