from utils.services.documento.validacao_service import (
    validar_cnpj,
    validar_cpf,
    documento_valido,
)


class DocumentoValidacaoController:

    @staticmethod
    def cnpj(valor):
        return validar_cnpj(valor)

    @staticmethod
    def cpf(valor):
        return validar_cpf(valor)

    @staticmethod
    def documento(valor):
        return documento_valido(valor)
