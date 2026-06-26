from datetime import datetime

def formatar_data_br(valor):
    valor = str(valor or "").strip()
    if not valor:
        return ""

    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(valor[:19], fmt).strftime("%d/%m/%Y")
        except Exception:
            pass

    return valor
