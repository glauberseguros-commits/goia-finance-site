import sqlite3

conn = sqlite3.connect("bd/gofinance.db")
cur = conn.cursor()

cur.execute("""
DELETE FROM empresas
WHERE id = 1
  AND (cnpj_cpf IS NULL OR cnpj_cpf = '')
""")

conn.commit()
conn.close()

print("Empresa duplicada sem CNPJ removida.")
