from __future__ import annotations

import json
import sqlite3
from typing import Any


def buscar_documento_por_chave_com_cursor(
    cursor: sqlite3.Cursor,
    empresa_id: int,
    chave_acesso: str,
):
    cursor.execute(
        """
        SELECT *
        FROM documentos
        WHERE empresa_id = ?
          AND chave_acesso_nfe = ?
        LIMIT 1
        """,
        (empresa_id, chave_acesso),
    )

    return cursor.fetchone()


def buscar_documento_por_hash_com_cursor(
    cursor: sqlite3.Cursor,
    empresa_id: int,
    hash_arquivo: str,
):
    cursor.execute(
        """
        SELECT *
        FROM documentos
        WHERE empresa_id = ?
          AND hash_arquivo = ?
        LIMIT 1
        """,
        (empresa_id, hash_arquivo),
    )

    return cursor.fetchone()


def _normalizar_valores_sql(dados: dict[str, Any]) -> list[Any]:
    valores = []

    for valor in dados.values():
        if isinstance(valor, (dict, list)):
            valores.append(json.dumps(valor, ensure_ascii=False))
        else:
            valores.append(valor)

    return valores


def inserir_documento_com_cursor(cursor: sqlite3.Cursor, **dados: Any):
    colunas = ", ".join(dados.keys())
    placeholders = ", ".join(["?"] * len(dados))
    valores = _normalizar_valores_sql(dados)

    cursor.execute(
        f"""
        INSERT INTO documentos
        ({colunas})
        VALUES
        ({placeholders})
        """,
        valores,
    )

    return cursor.lastrowid


def atualizar_documento_com_cursor(
    cursor: sqlite3.Cursor,
    documento_id: int,
    **dados: Any,
):
    if not dados:
        return

    campos = []
    valores = []

    for campo, valor in dados.items():
        campos.append(f"{campo}=?")

        if isinstance(valor, (dict, list)):
            valores.append(json.dumps(valor, ensure_ascii=False))
        else:
            valores.append(valor)

    valores.append(documento_id)

    cursor.execute(
        f"""
        UPDATE documentos
        SET {", ".join(campos)}
        WHERE id=?
        """,
        valores,
    )


def obter_documento_com_cursor(cursor: sqlite3.Cursor, documento_id: int):
    cursor.execute(
        "SELECT * FROM documentos WHERE id=?",
        (documento_id,),
    )

    return cursor.fetchone()
