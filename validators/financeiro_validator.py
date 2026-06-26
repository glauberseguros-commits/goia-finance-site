def valor_positivo(valor):
    try:
        return float(valor) > 0
    except Exception:
        return False

def valor_nao_negativo(valor):
    try:
        return float(valor) >= 0
    except Exception:
        return False
