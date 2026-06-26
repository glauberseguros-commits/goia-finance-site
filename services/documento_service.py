from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


DB_PATH = Path("bd/gofinance.db")


def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def buscar_documento_por_chave(
    empresa_id: int,
    chave_acesso: str,
):
    with conectar() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM documentos
            WHERE empresa_id = ?
              AND chave_acesso_nfe = ?
            LIMIT 1
            """,
            (empresa_id, chave_acesso),
        )

        return cur.fetchone()


def buscar_documento_por_hash(
    empresa_id: int,
    hash_arquivo: str,
):
    with conectar() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM documentos
            WHERE empresa_id = ?
              AND hash_arquivo = ?
            LIMIT 1
            """,
            (empresa_id, hash_arquivo),
        )

        return cur.fetchone()


def inserir_documento(**dados: Any):

    colunas = ", ".join(dados.keys())
    placeholders = ", ".join(["?"] * len(dados))

    valores = []

    for valor in dados.values():
        if isinstance(valor, (dict, list)):
            valores.append(json.dumps(valor, ensure_ascii=False))
        else:
            valores.append(valor)

    with conectar() as conn:
        cur = conn.cursor()

        cur.execute(
            f"""
            INSERT INTO documentos
            ({colunas})
            VALUES
            ({placeholders})
            """,
            valores,
        )

        conn.commit()

        return cur.lastrowid


def atualizar_documento(documento_id: int, **dados: Any):

    campos = []

    valores = []

    for campo, valor in dados.items():

        campos.append(f"{campo}=?")

        if isinstance(valor, (dict, list)):
            valores.append(json.dumps(valor, ensure_ascii=False))
        else:
            valores.append(valor)

    valores.append(documento_id)

    with conectar() as conn:
        cur = conn.cursor()

        cur.execute(
            f"""
            UPDATE documentos
            SET {", ".join(campos)}
            WHERE id=?
            """,
            valores,
        )

        conn.commit()


def obter_documento(documento_id: int):

    with conectar() as conn:

        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM documentos WHERE id=?",
            (documento_id,),
        )

        return cur.fetchone()
