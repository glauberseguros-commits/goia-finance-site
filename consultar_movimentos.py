import sqlite3

conn = sqlite3.connect("bd/gofinance.db")
cur = conn.cursor()

cur.execute("""
SELECT
    id,
    data_movimento,
    historico,
    valor,
    tipo,
    nome_origem
FROM movimentos_bancarios
ORDER BY id DESC
LIMIT 20
""")

for row in cur.fetchall():
    print(row)

conn.close()
