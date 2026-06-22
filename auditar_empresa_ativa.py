import sqlite3
import pandas as pd

conn = sqlite3.connect("bd/gofinance.db")

for tabela in ["empresas", "clientes", "fornecedores", "documentos", "contas_receber", "contas_pagar"]:
    try:
        df = pd.read_sql_query(f"""
        SELECT empresa_id, COUNT(*) AS qtd
        FROM {tabela}
        GROUP BY empresa_id
        ORDER BY empresa_id
        """, conn)
        print(f"\n{tabela}")
        print(df.to_string(index=False))
    except Exception as e:
        print(f"\n{tabela}: {e}")

conn.close()
