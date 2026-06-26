"""
Validação documental da GOIA.

Centraliza validações de CPF/CNPJ usadas pelo importador documental.
"""

from utils.services.documento.texto_service import somente_numeros



def validar_cnpj(valor):
    cnpj = somente_numeros(valor)

    if len(cnpj) != 14:
        return False

    if cnpj == cnpj[0] * 14:
        return False

    def calcular_digito(numeros, pesos):
        soma = sum(int(n) * p for n, p in zip(numeros, pesos))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    pesos1 = [5,4,3,2,9,8,7,6,5,4,3,2]
    pesos2 = [6,5,4,3,2,9,8,7,6,5,4,3,2]

    dig1 = calcular_digito(cnpj[:12], pesos1)
    dig2 = calcular_digito(cnpj[:12] + str(dig1), pesos2)

    return cnpj[-2:] == f"{dig1}{dig2}"

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
