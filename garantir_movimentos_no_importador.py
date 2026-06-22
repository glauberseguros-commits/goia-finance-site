from pathlib import Path

p = Path("pages/1_Importar_Documento.py")
txt = p.read_text(encoding="utf-8")

if "def garantir_estrutura_movimentos_bancarios():" not in txt:
    marcador = "garantir_estrutura_evidencias()"

    func = r'''

def garantir_estrutura_movimentos_bancarios():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS movimentos_bancarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            conta_bancaria_id INTEGER,
            data_movimento TEXT,
            descricao TEXT,
            documento TEXT,
            valor REAL,
            tipo TEXT,
            conciliado INTEGER DEFAULT 0,
            conta_receber_id INTEGER,
            conta_pagar_id INTEGER,
            origem TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


garantir_estrutura_movimentos_bancarios()
'''

    txt = txt.replace(marcador, marcador + func)

p.write_text(txt, encoding="utf-8")

print("Estrutura de movimentos bancários garantida no importador.")
