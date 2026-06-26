import re

def apenas_digitos(valor):
    return re.sub(r"\D", "", str(valor or ""))

def cnpj_valido(cnpj):
    cnpj = apenas_digitos(cnpj)
    return len(cnpj) == 14

def cpf_valido(cpf):
    cpf = apenas_digitos(cpf)
    return len(cpf) == 11

def documento_valido(valor):
    doc = apenas_digitos(valor)
    return len(doc) in [11, 14]
