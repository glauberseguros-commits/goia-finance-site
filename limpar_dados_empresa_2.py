import sqlite3

conn = sqlite3.connect("bd/gofinance.db")
cur = conn.cursor()

for tabela in [
    "conciliacoes",
    "movimentos_bancarios",
    "processo_evidencias",
    "processo_pendencias",
    "processo_documentos",
    "processos_documentais",
    "contas_receber",
    "contas_pagar",
    "vendas_itens",
    "vendas",
    "compras_itens",
    "compras",
    "produtos",
    "fornecedores",
    "clientes",
    "documentos"
]:
    cur.execute(f"DELETE FROM {tabela} WHERE empresa_id = 2")
    print(f"{tabela}: {cur.rowcount} apagado(s)")

conn.commit()
conn.close()

print("Base de teste da empresa 2 limpa.")
