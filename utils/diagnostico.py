from pathlib import Path
import os
import sqlite3

from utils.db import caminho_banco


def diagnostico_banco():
    db = caminho_banco()

    info = {
        "goia_db_path_env": os.getenv("GOIA_DB_PATH", ""),
        "banco_ativo": str(db),
        "banco_existe": db.exists(),
        "pasta_existe": db.parent.exists(),
        "banco_absoluto": str(db.resolve()),
        "modo": "Persistente" if str(db).replace("\\","/").startswith("/data/") else "Fallback",
    }

    if db.exists():
        info["tamanho_bytes"] = db.stat().st_size

        conn = sqlite3.connect(db)
        cur = conn.cursor()

        tabelas = [
            r[0]
            for r in cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]

        info["tabelas"] = {}

        for tabela in tabelas:
            try:
                qtd = cur.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
            except Exception:
                qtd = None

            info["tabelas"][tabela] = qtd

        conn.close()

    return info
