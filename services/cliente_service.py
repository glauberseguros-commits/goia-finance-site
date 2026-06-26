from __future__ import annotations

import sqlite3


def buscar_cliente_por_documento_com_cursor(
    cursor: sqlite3.Cursor,
    empresa_id: int,
    documento: str,
):
    cursor.execute(
        """
        SELECT id
        FROM clientes
        WHERE empresa_id = ?
          AND cnpj_cpf = ?
        LIMIT 1
        """,
        (empresa_id, documento),
    )

    return cursor.fetchone()


def criar_cliente_com_cursor(
    cursor: sqlite3.Cursor,
    empresa_id: int,
    nome: str,
    documento: str,
    origem_cadastro: str = "Importação documental",
):
    cursor.execute(
        """
        INSERT INTO clientes (
            empresa_id,
            nome,
            cnpj_cpf,
            origem_cadastro
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            empresa_id,
            nome,
            documento,
            origem_cadastro,
        ),
    )

    return cursor.lastrowid


def obter_ou_criar_cliente_com_cursor(
    cursor: sqlite3.Cursor,
    empresa_id: int,
    documento: str,
    nome: str,
    normalizar_documento_fn,
    documento_entidade_valido_fn,
    nome_entidade_valido_fn,
):
    documento = normalizar_documento_fn(documento)
    nome = (nome or "").strip()

    if not documento_entidade_valido_fn(documento):
        return None

    if not nome_entidade_valido_fn(nome):
        return None

    existente = buscar_cliente_por_documento_com_cursor(
        cursor,
        empresa_id,
        documento,
    )

    if existente:
        return existente[0]

    return criar_cliente_com_cursor(
        cursor,
        empresa_id,
        nome,
        documento,
    )
