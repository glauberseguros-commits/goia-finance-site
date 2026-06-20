import sqlite3

conn = sqlite3.connect("bd/gofinance.db")
cur = conn.cursor()

cur.execute("""
SELECT
    id,
    descricao,
    valor,
    status,
    data_vencimento
FROM contas_receber
""")

for linha in cur.fetchall():
    print(linha)

conn.close()
