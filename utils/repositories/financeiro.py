from utils.db import conectar_banco

def resumo_financeiro(empresa_id=None):
    conn = conectar_banco()
    cur = conn.cursor()
    try:
        params = (empresa_id,) if empresa_id else ()
        where = "WHERE empresa_id = ?" if empresa_id else ""

        receber = cur.execute(f"SELECT COALESCE(SUM(valor),0) FROM contas_receber {where}", params).fetchone()[0]
        pagar = cur.execute(f"SELECT COALESCE(SUM(valor),0) FROM contas_pagar {where}", params).fetchone()[0]

        return {
            "receber": receber or 0,
            "pagar": pagar or 0,
            "saldo": (receber or 0) - (pagar or 0),
        }
    finally:
        conn.close()
