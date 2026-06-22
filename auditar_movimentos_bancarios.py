import sqlite3

conn = sqlite3.connect("bd/gofinance.db")
cur = conn.cursor()

cur.execute("PRAGMA table_info(movimentos_bancarios)")

for row in cur.fetchall():
    print(row)

conn.close()
