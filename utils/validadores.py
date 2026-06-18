def apenas_digitos(valor):
    return ''.join(filter(str.isdigit, str(valor or "")))

def validar_cnpj(cnpj):
    cnpj = apenas_digitos(cnpj)

    if len(cnpj) != 14:
        return False

    if cnpj == cnpj[0] * 14:
        return False

    def calcular_digito(cnpj_base, pesos):
        soma = sum(int(digito) * peso for digito, peso in zip(cnpj_base, pesos))
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)

    primeiro = calcular_digito(cnpj[:12], [5,4,3,2,9,8,7,6,5,4,3,2])
    segundo = calcular_digito(cnpj[:12] + primeiro, [6,5,4,3,2,9,8,7,6,5,4,3,2])

    return cnpj[-2:] == primeiro + segundo

def validar_cpf(cpf):
    cpf = apenas_digitos(cpf)

    if len(cpf) != 11:
        return False

    if cpf == cpf[0] * 11:
        return False

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = 0 if soma % 11 < 2 else 11 - (soma % 11)

    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = 0 if soma % 11 < 2 else 11 - (soma % 11)

    return cpf[-2:] == f"{d1}{d2}"
