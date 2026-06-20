import sqlite3

conn = sqlite3.connect("bd/gofinance.db")
cur = conn.cursor()

for tabela in ["contas_receber", "contas_pagar", "movimentos_bancarios", "documentos"]:
    print("\n===", tabela, "===")
    cur.execute(f"SELECT * FROM {tabela}")
    cols = [d[0] for d in cur.description]
    print(cols)
    for row in cur.fetchall():
        print(row)

conn.close()
