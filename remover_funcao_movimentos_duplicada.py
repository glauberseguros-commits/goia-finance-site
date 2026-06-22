from pathlib import Path
import re

p = Path("pages/1_Importar_Documento.py")
txt = p.read_text(encoding="utf-8")

padrao = r'\n+def garantir_estrutura_movimentos_bancarios\(\):\n    conn = conectar\(\)\n    cur = conn\.cursor\(\)\n\n    cur\.execute\("""\n        CREATE TABLE IF NOT EXISTS movimentos_bancarios \(\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n            empresa_id INTEGER,\n            data_movimento TEXT,\n            descricao TEXT,\n            documento TEXT,\n            valor REAL,\n            tipo TEXT,\n            conciliado INTEGER DEFAULT 0,\n            origem TEXT,\n            criado_em TEXT DEFAULT CURRENT_TIMESTAMP\n        \)\n    """\)\n\n    conn\.commit\(\)\n    conn\.close\(\)\n\n\n'

txt2, n = re.subn(padrao, "\n\n", txt, count=1)

if n != 1:
    raise SystemExit(f"Não removi a função duplicada. Ocorrências removidas: {n}")

p.write_text(txt2, encoding="utf-8")
print("Função duplicada removida.")
