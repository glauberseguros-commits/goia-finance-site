from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.db import conectar_banco


def _row_to_dict(cursor, row):
    if row is None:
        return None

    colunas = [desc[0] for desc in cursor.description]
    return dict(zip(colunas, row))


def listar_empresas() -> List[Dict[str, Any]]:
    conn = conectar_banco()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM empresas
        ORDER BY id DESC
    """)

    rows = cur.fetchall()
    colunas = [desc[0] for desc in cur.description]

    conn.close()

    return [dict(zip(colunas, row)) for row in rows]


def buscar_empresa_por_id(empresa_id: int) -> Optional[Dict[str, Any]]:
    conn = conectar_banco()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM empresas
        WHERE id = ?
        LIMIT 1
    """, (empresa_id,))

    row = cur.fetchone()
    empresa = _row_to_dict(cur, row)

    conn.close()

    return empresa


def buscar_empresa_por_cnpj(cnpj: str) -> Optional[Dict[str, Any]]:
    cnpj_limpo = "".join(filter(str.isdigit, str(cnpj or "")))

    conn = conectar_banco()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM empresas
        WHERE REPLACE(REPLACE(REPLACE(REPLACE(COALESCE(cnpj_cpf, cnpj, ''),'.',''),'/',''),'-',''),' ','') = ?
        LIMIT 1
    """, (cnpj_limpo,))

    row = cur.fetchone()
    empresa = _row_to_dict(cur, row)

    conn.close()

    return empresa


def empresa_ativa_existe(empresa_id: int) -> bool:
    empresa = buscar_empresa_por_id(empresa_id)

    if not empresa:
        return False

    status = str(empresa.get("status_assinatura") or "Ativa").strip()

    return status in ["Ativa", "Teste", "VIP"]


def atualizar_status_empresa(empresa_id: int, status: str, motivo: str = "") -> None:
    conn = conectar_banco()
    cur = conn.cursor()

    cur.execute("""
        UPDATE empresas
        SET status_assinatura = ?,
            motivo_bloqueio = ?,
            atualizado_em = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (status, motivo, empresa_id))

    conn.commit()
    conn.close()


def cancelar_empresa(empresa_id: int, motivo: str = "Cancelada pelo Admin GOIA") -> None:
    atualizar_status_empresa(empresa_id, "Cancelada", motivo)


def excluir_empresa_fisicamente(empresa_id: int) -> None:
    """
    Uso restrito. Mantido apenas para manutenção técnica.
    No fluxo normal do Admin, usar cancelar_empresa().
    """
    conn = conectar_banco()
    cur = conn.cursor()

    cur.execute("DELETE FROM empresas WHERE id = ?", (empresa_id,))

    conn.commit()
    conn.close()


def registrar_timestamp_atualizacao(empresa_id: int) -> None:
    conn = conectar_banco()
    cur = conn.cursor()

    cur.execute("""
        UPDATE empresas
        SET atualizado_em = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (empresa_id,))

    conn.commit()
    conn.close()
