from utils.db import conectar_banco

def listar_usuarios():
    conn = conectar_banco()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM usuarios ORDER BY id DESC")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]
    finally:
        conn.close()
