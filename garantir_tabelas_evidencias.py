import sqlite3

conn = sqlite3.connect("bd/gofinance.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS evidencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER,
    processo_id INTEGER,
    documento_id INTEGER,
    conta_receber_id INTEGER,
    conta_pagar_id INTEGER,
    tipo_evidencia TEXT,
    descricao TEXT,
    origem TEXT,
    valor REAL,
    data_referencia TEXT,
    status TEXT DEFAULT 'Ativa',
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS processo_evidencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER NOT NULL,
    processo_id INTEGER NOT NULL,
    documento_id INTEGER,
    tipo_evidencia TEXT NOT NULL,
    descricao TEXT,
    valor REAL,
    data_evidencia TEXT,
    origem TEXT,
    status TEXT DEFAULT 'Validada',
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

print("OK - evidencias")
print("OK - processo_evidencias")

conn.close()
