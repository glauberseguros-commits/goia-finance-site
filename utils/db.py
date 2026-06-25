
from pathlib import Path
import os
import sqlite3

def caminho_banco():
    db_path = os.getenv("GOIA_DB_PATH")

    if db_path:
        path = Path(db_path)
    elif Path("/data").exists():
        path = Path("/data/gofinance.db")
    else:
        path = Path("bd/gofinance.db")

    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def conectar_banco(timeout=30):
    conn = sqlite3.connect(caminho_banco(), timeout=timeout)
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn