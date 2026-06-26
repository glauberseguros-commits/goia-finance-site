from datetime import datetime
import platform
import sqlite3

from utils.db import caminho_banco


def health_check():
    db = caminho_banco()

    info = {
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "python": platform.python_version(),
        "sistema": platform.system(),
        "banco": str(db),
        "banco_existe": db.exists(),
        "tamanho_mb": round(db.stat().st_size / 1024 / 1024, 2) if db.exists() else 0,
        "sqlite": sqlite3.sqlite_version,
    }

    try:
        conn = sqlite3.connect(db)

        info["integrity_check"] = conn.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        info["foreign_keys"] = conn.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

        info["journal_mode"] = conn.execute(
            "PRAGMA journal_mode"
        ).fetchone()[0]

        conn.close()

    except Exception as e:
        info["erro"] = str(e)

    return info
