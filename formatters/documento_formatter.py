import re

def apenas_digitos(valor):
    return re.sub(r"\D", "", str(valor or ""))

def formatar_cnpj(valor):
    n = apenas_digitos(valor)
    if len(n) == 14:
        return f"{n[:2]}.{n[2:5]}.{n[5:8]}/{n[8:12]}-{n[12:]}"
    return str(valor or "")

def formatar_cpf(valor):
    n = apenas_digitos(valor)
    if len(n) == 11:
        return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}"
    return str(valor or "")

def formatar_documento(valor):
    n = apenas_digitos(valor)
    if len(n) == 14:
        return formatar_cnpj(n)
    if len(n) == 11:
        return formatar_cpf(n)
    return str(valor or "")
