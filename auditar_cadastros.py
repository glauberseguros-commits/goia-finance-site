import sqlite3
import pandas as pd

conn = sqlite3.connect("bd/gofinance.db")

for tabela in ["clientes","fornecedores"]:

    print("\n")
    print("=" * 80)
    print(tabela.upper())
    print("=" * 80)

    try:
        df = pd.read_sql(
            f"SELECT * FROM {tabela}",
            conn
        )

        print(df.to_string(index=False))

    except Exception as e:
        print(e)

conn.close()
