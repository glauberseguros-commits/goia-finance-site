from pathlib import Path

p = Path("pages/1_Importar_Documento.py")
txt = p.read_text(encoding="utf-8")

alvo = '''

garantir_estrutura_evidencias()
'''

insercao = '''

garantir_estrutura_evidencias()


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

if "def garantir_estrutura_movimentos_bancarios():" not in txt:
    if alvo not in txt:
        raise SystemExit("Ponto de inserção não encontrado: garantir_estrutura_evidencias()")
    txt = txt.replace(alvo, insercao, 1)

p.write_text(txt, encoding="utf-8", newline="\n")

print("Estrutura de movimentos bancários inserida corretamente.")
