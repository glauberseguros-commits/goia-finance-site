import re

def formatar_telefone(valor):
    n = re.sub(r"\D", "", str(valor or ""))

    if len(n) == 11:
        return f"{n[:2]} - {n[2]} {n[3:7]}-{n[7:]}"
    if len(n) == 10:
        return f"{n[:2]} - {n[2:6]}-{n[6:]}"
    if len(n) == 9:
        return f"{n[0]} {n[1:5]}-{n[5:]}"
    if len(n) == 8:
        return f"{n[:4]}-{n[4:]}"

    return str(valor or "")
