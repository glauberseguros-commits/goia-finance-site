import sqlite3
import pandas as pd

conn = sqlite3.connect("bd/gofinance.db")

df = pd.read_sql("""
SELECT
    id,
    nome,
    cnpj_cpf
FROM clientes
ORDER BY id DESC
""", conn)

print(df.to_string(index=False))

conn.close()
