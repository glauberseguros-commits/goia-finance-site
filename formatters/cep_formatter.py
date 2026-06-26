import re

def formatar_cep(valor):
    n = re.sub(r"\D", "", str(valor or ""))
    if len(n) == 8:
        return f"{n[:5]}-{n[5:]}"
    return str(valor or "")
