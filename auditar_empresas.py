import sqlite3
import pandas as pd

conn = sqlite3.connect("bd/gofinance.db")

print("="*80)
print("EMPRESAS")
print("="*80)

try:
    df = pd.read_sql("""
        SELECT *
        FROM empresas
    """, conn)

    print(df.to_string(index=False))
except Exception as e:
    print(e)

print()
print("="*80)
print("CLIENTES POR EMPRESA")
print("="*80)

try:
    df = pd.read_sql("""
        SELECT
            empresa_id,
            COUNT(*) qtd
        FROM clientes
        GROUP BY empresa_id
    """, conn)

    print(df.to_string(index=False))
except Exception as e:
    print(e)

conn.close()
