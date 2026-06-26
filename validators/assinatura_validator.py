STATUS_ASSINATURA_VALIDOS = [
    "Teste",
    "Ativa",
    "VIP",
    "Suspensa",
    "Bloqueada",
    "Cancelada",
    "Expirada",
    "Inativa",
]

def status_assinatura_valido(status):
    return str(status or "").strip() in STATUS_ASSINATURA_VALIDOS
