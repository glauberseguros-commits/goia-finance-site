import sqlite3

conn = sqlite3.connect("bd/gofinance.db")
cur = conn.cursor()

for tabela in [
    "extratos_bancarios",
    "movimentos_bancarios",
    "conciliacoes"
]:
    try:
        cur.execute(f"PRAGMA table_info({tabela})")
        cols = cur.fetchall()

        print("\n", tabela.upper())
        print("EXISTE:", len(cols) > 0)

        for c in cols:
            print(c[1], c[2])

    except Exception as e:
        print(tabela, e)

conn.close()
