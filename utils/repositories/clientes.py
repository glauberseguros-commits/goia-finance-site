from utils.db import conectar_banco

def listar_clientes(empresa_id=None):
    conn = conectar_banco()
    cur = conn.cursor()
    try:
        if empresa_id:
            cur.execute("SELECT * FROM clientes WHERE empresa_id = ? ORDER BY id DESC", (empresa_id,))
        else:
            cur.execute("SELECT * FROM clientes ORDER BY id DESC")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]
    finally:
        conn.close()
