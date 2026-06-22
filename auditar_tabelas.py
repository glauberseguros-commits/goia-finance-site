import sqlite3

conn = sqlite3.connect("bd/gofinance.db")
cur = conn.cursor()

for tabela in [
    "clientes",
    "fornecedores",
    "documentos",
    "compras",
    "compras_itens",
    "vendas",
    "vendas_itens",
    "contas_receber",
    "contas_pagar",
    "produtos",
    "processos_documentais",
    "processo_documentos",
    "processo_pendencias",
    "empresas"
]:
    print(f"\n=== {tabela} ===")

    try:
        cur.execute(f"PRAGMA table_info({tabela})")

        for col in cur.fetchall():
            print(col[1], col[2])

    except Exception as e:
        print("ERRO:", e)

conn.close()
