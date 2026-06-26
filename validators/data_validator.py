from datetime import datetime

def data_valida(valor):
    valor = str(valor or "").strip()
    if not valor:
        return False

    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            datetime.strptime(valor[:19], fmt)
            return True
        except Exception:
            pass

    return False
