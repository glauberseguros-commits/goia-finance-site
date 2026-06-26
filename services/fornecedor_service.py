from __future__ import annotations

import sqlite3


def buscar_fornecedor_por_documento_com_cursor(
    cursor: sqlite3.Cursor,
    empresa_id: int,
    documento: str,
):
    cursor.execute(
        """
        SELECT id
        FROM fornecedores
        WHERE empresa_id = ?
          AND cnpj = ?
        LIMIT 1
        """,
        (empresa_id, documento),
    )
    return cursor.fetchone()


def criar_fornecedor_com_cursor(
    cursor: sqlite3.Cursor,
    empresa_id: int,
    nome: str,
    documento: str,
):
    cursor.execute(
        """
        INSERT INTO fornecedores (
            empresa_id,
            nome,
            cnpj,
            categoria_padrao,
            tipo_padrao,
            origem_cadastro
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            empresa_id,
            nome,
            documento,
            "A classificar",
            "Pagar",
            "Importação documental",
        ),
    )

    return cursor.lastrowid


def obter_ou_criar_fornecedor_com_cursor(
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

    existente = buscar_fornecedor_por_documento_com_cursor(
        cursor,
        empresa_id,
        documento,
    )

    if existente:
        return existente[0]

    return criar_fornecedor_com_cursor(
        cursor,
        empresa_id,
        nome,
        documento,
    )
