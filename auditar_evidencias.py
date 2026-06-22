import sqlite3
import pandas as pd

conn = sqlite3.connect("bd/gofinance.db")

for tabela in ["evidencias", "processo_evidencias"]:
    print("\n" + "=" * 80)
    print(tabela.upper())
    print("=" * 80)

    df = pd.read_sql_query(
        f"PRAGMA table_info({tabela})",
        conn
    )

    print(df.to_string(index=False))

conn.close()
