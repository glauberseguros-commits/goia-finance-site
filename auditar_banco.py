import sqlite3

conn = sqlite3.connect("bd/gofinance.db")
cur = conn.cursor()

cur.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
ORDER BY name
""")

tabelas = [x[0] for x in cur.fetchall()]

for tabela in tabelas:

    print("\n" + "=" * 80)
    print(tabela.upper())
    print("=" * 80)

    cur.execute(f"PRAGMA table_info({tabela})")

    for col in cur.fetchall():
        print(f"{col[1]} | {col[2]}")

conn.close()
