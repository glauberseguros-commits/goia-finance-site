"""
Serviço central de gerenciamento de assinantes da GOIA.

Este módulo concentrará toda a regra de negócio referente às empresas
assinantes da plataforma.
"""

from utils.repositories.empresas import (
    listar_empresas,
    buscar_empresa_por_id,
    buscar_empresa_por_cnpj,
    atualizar_status_empresa,
    cancelar_empresa,
)

from validators.documento_validator import documento_valido
from validators.email_validator import email_valido
from validators.telefone_validator import telefone_valido


def listar_assinantes():
    return listar_empresas()


def obter_assinante(empresa_id):
    return buscar_empresa_por_id(empresa_id)


def localizar_por_cnpj(cnpj):
    return buscar_empresa_por_cnpj(cnpj)


def validar_dados_cadastro(cnpj, email, telefone):

    erros = []

    if not documento_valido(cnpj):
        erros.append("CNPJ/CPF inválido.")

    if email and not email_valido(email):
        erros.append("E-mail inválido.")

    if telefone and not telefone_valido(telefone):
        erros.append("Telefone inválido.")

    return erros


def bloquear_assinante(empresa_id, motivo="Bloqueado pelo Administrador"):
    atualizar_status_empresa(
        empresa_id,
        "Bloqueada",
        motivo
    )


def suspender_assinante(empresa_id, motivo="Suspensa pelo Administrador"):
    atualizar_status_empresa(
        empresa_id,
        "Suspensa",
        motivo
    )


def cancelar_assinante(
    empresa_id,
    motivo="Cancelada pelo Administrador GOIA"
):
    cancelar_empresa(
        empresa_id,
        motivo
    )
