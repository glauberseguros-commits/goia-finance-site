import sqlite3

conn = sqlite3.connect("bd/gofinance.db")
cur = conn.cursor()

for tabela in [
    "faturas_cartao",
    "lancamentos_caixa",
    "processo_pendencias"
]:
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

        cur.execute(f"SELECT * FROM {tabela}")
        rows = cur.fetchall()

        for r in rows:
            print(r)

    except Exception as e:
        print("ERRO:", e)

conn.close()
