import sqlite3
import pandas as pd

conn = sqlite3.connect("bd/gofinance.db")

df = pd.read_sql_query("""
SELECT
    id,
    tipo_documento,
    direcao,
    nome_emitente,
    cnpj_emitente,
    nome_destinatario,
    cnpj_destinatario,
    valor,
    numero_nfe,
    serie_nfe
FROM documentos
ORDER BY id DESC
LIMIT 20
""", conn)

print(df.to_string(index=False))

conn.close()
