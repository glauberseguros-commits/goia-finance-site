import sqlite3
import pandas as pd

DB_PATH = "bd/gofinance.db"

tabelas = [
    "clientes",
    "documentos",
    "processos_documentais",
    "contas_receber",
    "evidencias",
    "pendencias",
]

conn = sqlite3.connect(DB_PATH)

for tabela in tabelas:
    print("\n" + "=" * 80)
    print(f"TABELA: {tabela}")
    print("=" * 80)

    try:
        df = pd.read_sql_query(f"PRAGMA table_info({tabela})", conn)
        if df.empty:
            print("Tabela não encontrada.")
        else:
            print(df[["cid", "name", "type", "notnull", "dflt_value", "pk"]].to_string(index=False))
    except Exception as e:
        print(f"Erro ao auditar {tabela}: {e}")

conn.close()
