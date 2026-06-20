import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

DB = Path("bd/gofinance.db")
BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(exist_ok=True)

agora = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = BACKUP_DIR / f"gofinance_backup_antes_limpeza_{agora}.db"

shutil.copy2(DB, backup)

conn = sqlite3.connect(DB)
cur = conn.cursor()

# ordem importa por causa dos vínculos
tabelas_limpar = [
    "conciliacoes",
    "movimentos_bancarios",
    "extratos_bancarios",
    "processo_pendencias",
    "processo_documentos",
    "processos_documentais",
    "contas_receber",
    "contas_pagar",
    "compras",
    "vendas",
    "documentos",
    "produtos",
    "clientes",
    "fornecedores"
]

for tabela in tabelas_limpar:
    try:
        cur.execute(f"DELETE FROM {tabela} WHERE empresa_id = 1")
        print(f"Limpa: {tabela} -> {cur.rowcount} registro(s)")
    except Exception as e:
        print(f"ERRO em {tabela}: {e}")

conn.commit()

print("\nConferência após limpeza:")
for tabela in tabelas_limpar:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {tabela}")
        print(f"{tabela}: {cur.fetchone()[0]}")
    except Exception as e:
        print(f"{tabela}: ERRO - {e}")

conn.close()

print(f"\nBackup criado em: {backup}")
