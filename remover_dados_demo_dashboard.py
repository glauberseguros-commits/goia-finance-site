from pathlib import Path

arquivo = Path("app.py")
texto = arquivo.read_text(encoding="utf-8")

texto = texto.replace(
'''    return pd.DataFrame([
        {"data": "2026-06-01", "tipo": "Receber", "descricao": "Cliente A", "categoria": "Vendas", "valor": 1500.00, "status": "Recebido"},
        {"data": "2026-06-02", "tipo": "Receber", "descricao": "Cliente B", "categoria": "Vendas", "valor": 2200.00, "status": "Pendente"},
        {"data": "2026-06-03", "tipo": "Pagar", "descricao": "Fornecedor X", "categoria": "Fornecedores", "valor": -800.00, "status": "Pago"},
    ])''',
'''    return pd.DataFrame(columns=[
        "data",
        "tipo",
        "descricao",
        "categoria",
        "valor",
        "status"
    ])'''
)

texto = texto.replace(
'''html = html.replace("__RECEBIMENTOS__", moeda(recebimentos))
html = html.replace("__PAGAMENTOS__", moeda(pagamentos))
html = html.replace("__SALDO__", moeda(saldo))
html = html.replace("__PENDENCIAS__", str(pendencias))''',
'''html = html.replace("__RECEBIMENTOS__", moeda(recebimentos))
html = html.replace("__PAGAMENTOS__", moeda(pagamentos))
html = html.replace("__SALDO__", moeda(saldo))
html = html.replace("__PENDENCIAS__", str(pendencias))'''
)

arquivo.write_text(texto, encoding="utf-8")
print("OK")
