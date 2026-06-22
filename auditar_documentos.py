import sqlite3
import pandas as pd

conn = sqlite3.connect("bd/gofinance.db")

df = pd.read_sql("""
SELECT
    id,
    tipo_documento,
    direcao,
    nome_emitente,
    cnpj_emitente,
    nome_destinatario,
    cnpj_destinatario,
    valor
FROM documentos
ORDER BY id DESC
""", conn)

print(df.to_string(index=False))

conn.close()
