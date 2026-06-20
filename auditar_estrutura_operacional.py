import sqlite3

conn = sqlite3.connect("bd/gofinance.db")
cur = conn.cursor()

for tabela in ["compras","vendas","conciliacoes"]:
    print("\n====================")
    print(tabela.upper())
    print("====================")

    try:
        cur.execute(f"PRAGMA table_info({tabela})")

        cols = cur.fetchall()

        for c in cols:
            print(c)

        cur.execute(f"SELECT COUNT(*) FROM {tabela}")
        print("\nREGISTROS:", cur.fetchone()[0])

    except Exception as e:
        print("ERRO:", e)

conn.close()
