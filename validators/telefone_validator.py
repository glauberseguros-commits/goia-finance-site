import re

def telefone_valido(telefone):
    numeros = re.sub(r"\D", "", str(telefone or ""))
    return len(numeros) in [10, 11]
