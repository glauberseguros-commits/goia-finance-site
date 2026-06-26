"""
Validação documental da GOIA.

Centraliza validações de CPF/CNPJ usadas pelo importador documental.
"""

from utils.services.documento.texto_service import somente_numeros


def validar_cnpj(valor):
    cnpj = somente_numeros(valor)

    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    def calc(digs):
        pesos = list(range(len(digs) - 7, 1, -1))
        soma = sum(int(d) * p for d, p in zip(digs, pesos))
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)

    return cnpj[-2:] == calc(cnpj[:12]) + calc(cnpj[:13])


def validar_cpf(valor):
    cpf = somente_numeros(valor)

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    def calc(digs):
        soma = sum(int(d) * (len(digs) + 1 - i) for i, d in enumerate(digs))
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)

    return cpf[-2:] == calc(cpf[:9]) + calc(cpf[:10])


def documento_valido(valor):
    nums = somente_numeros(valor)
    return validar_cnpj(nums) or validar_cpf(nums)
