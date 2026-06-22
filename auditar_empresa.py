import sqlite3
import pandas as pd

conn = sqlite3.connect("bd/gofinance.db")

df = pd.read_sql_query("""
SELECT
    id,
    nome,
    cnpj_cpf
FROM empresas
ORDER BY id
""", conn)

print(df.to_string(index=False))

conn.close()
