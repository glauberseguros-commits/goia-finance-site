from datetime import datetime

def formatar_data(data):
    if not data:
        return ""

    try:
        return datetime.strptime(
            str(data)[:10],
            "%Y-%m-%d"
        ).strftime("%d/%m/%Y")
    except:
        return str(data)

def formatar_moeda(valor):
    if valor is None:
        return "R$ 0,00"

    texto = f"R$ {float(valor):,.2f}"
    texto = texto.replace(",", "X")
    texto = texto.replace(".", ",")
    texto = texto.replace("X", ".")

    return texto

def formatar_percentual(valor):
    if valor is None:
        return "0,00%"

    texto = f"{float(valor):,.2f}%"
    texto = texto.replace(",", "X")
    texto = texto.replace(".", ",")
    texto = texto.replace("X", ".")

    return texto

def formatar_cnpj(cnpj):
    if not cnpj:
        return ""

    numeros = ''.join(filter(str.isdigit, str(cnpj)))

    if len(numeros) != 14:
        return cnpj

    return (
        f"{numeros[:2]}."
        f"{numeros[2:5]}."
        f"{numeros[5:8]}/"
        f"{numeros[8:12]}-"
        f"{numeros[12:]}"
    )

def formatar_cpf(cpf):
    if not cpf:
        return ""

    numeros = ''.join(filter(str.isdigit, str(cpf)))

    if len(numeros) != 11:
        return cpf

    return (
        f"{numeros[:3]}."
        f"{numeros[3:6]}."
        f"{numeros[6:9]}-"
        f"{numeros[9:]}"
    )
