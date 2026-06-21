
import re

def somente_numeros(valor):
    return re.sub(r"\D", "", valor or "")

def limpar_cnpj(valor):
    n = somente_numeros(valor)
    return n if len(n) == 14 else n

def limpar_cpf(valor):
    n = somente_numeros(valor)
    return n if len(n) == 11 else n

def limpar_telefone(valor):
    n = somente_numeros(valor)
    return n

def limpar_cep(valor):
    n = somente_numeros(valor)
    return n if len(n) == 8 else n

def telefone_valido(valor):
    n = limpar_telefone(valor)
    return len(n) in (10, 11)

def formatar_cnpj(valor):
    n = somente_numeros(valor)
    if len(n) == 14:
        return f"{n[:2]}.{n[2:5]}.{n[5:8]}/{n[8:12]}-{n[12:]}"
    return valor or ""

def formatar_cpf(valor):
    n = somente_numeros(valor)
    if len(n) == 11:
        return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}"
    return valor or ""

def formatar_telefone(valor):
    n = somente_numeros(valor)
    if len(n) == 11:
        return f"({n[:2]}) {n[2:7]}-{n[7:]}"
    if len(n) == 10:
        return f"({n[:2]}) {n[2:6]}-{n[6:]}"
    return valor or ""

def formatar_cep(valor):
    n = somente_numeros(valor)
    if len(n) == 8:
        return f"{n[:2]}.{n[2:5]}-{n[5:]}"
    return valor or ""
