import sqlite3
from datetime import datetime
from utils.processos import atualizar_processo_por_baixa_financeira

DB_PATH = "bd/gofinance.db"


def baixar_conta_receber(
    conta_receber_id,
    empresa_id,
    valor_baixado=None,
    observacao=""
):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT valor, status, documento_id
        FROM contas_receber
        WHERE id = ?
          AND empresa_id = ?
    """, (conta_receber_id, empresa_id))

    registro = cur.fetchone()

    if not registro:
        conn.close()
        raise Exception("Conta a receber não encontrada.")

    valor_original, status, documento_id = registro

    if status == "Baixada":
        conn.close()
        raise Exception("Conta já está baixada.")

    if valor_baixado is None:
        valor_baixado = valor_original

    cur.execute("""
        UPDATE contas_receber
        SET status = 'Baixada',
            data_baixa = ?,
            valor_baixado = ?,
            observacao_baixa = ?
        WHERE id = ?
          AND empresa_id = ?
    """, (
        datetime.now().strftime("%Y-%m-%d"),
        valor_baixado,
        observacao,
        conta_receber_id,
        empresa_id
    ))

    cur.execute("""
        INSERT INTO recebimentos (
            conta_receber_id,
            valor_recebido,
            data_recebimento,
            forma_recebimento,
            empresa_id,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        conta_receber_id,
        valor_baixado,
        datetime.now().strftime("%Y-%m-%d"),
        "Baixa manual",
        empresa_id,
        "Baixado"
    ))

    atualizar_processo_por_baixa_financeira(
        cur,
        documento_id,
        empresa_id,
        "receber"
    )

    conn.commit()
    conn.close()

    return True


def baixar_conta_pagar(
    conta_pagar_id,
    empresa_id,
    valor_baixado=None,
    observacao=""
):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT valor, status, documento_id
        FROM contas_pagar
        WHERE id = ?
          AND empresa_id = ?
    """, (conta_pagar_id, empresa_id))

    registro = cur.fetchone()

    if not registro:
        conn.close()
        raise Exception("Conta a pagar não encontrada.")

    valor_original, status, documento_id = registro

    if status == "Baixada":
        conn.close()
        raise Exception("Conta já está baixada.")

    if valor_baixado is None:
        valor_baixado = valor_original

    cur.execute("""
        UPDATE contas_pagar
        SET status = 'Baixada',
            data_baixa = ?,
            valor_baixado = ?,
            observacao_baixa = ?
        WHERE id = ?
          AND empresa_id = ?
    """, (
        datetime.now().strftime("%Y-%m-%d"),
        valor_baixado,
        observacao,
        conta_pagar_id,
        empresa_id
    ))

    cur.execute("""
        INSERT INTO pagamentos (
            conta_pagar_id,
            valor_pago,
            data_pagamento,
            forma_pagamento,
            empresa_id
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        conta_pagar_id,
        valor_baixado,
        datetime.now().strftime("%Y-%m-%d"),
        "Baixa manual",
        empresa_id
    ))

    atualizar_processo_por_baixa_financeira(
        cur,
        documento_id,
        empresa_id,
        "pagar"
    )

    conn.commit()
    conn.close()

    return True