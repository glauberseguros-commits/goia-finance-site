import sqlite3
import pandas as pd

conn = sqlite3.connect("bd/gofinance.db")

for tabela in ["documentos", "clientes", "fornecedores", "vendas", "contas_receber"]:
    print()
    print("=" * 100)
    print(tabela.upper())
    print("=" * 100)

    try:
        df = pd.read_sql(f"SELECT * FROM {tabela} ORDER BY id DESC LIMIT 20", conn)
        print(df.to_string(index=False))
    except Exception as e:
        print("ERRO:", e)

conn.close()
