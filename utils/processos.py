import sqlite3

DB_PATH = "bd/gofinance.db"

def atualizar_status_processo_por_id(cur, processo_id, empresa_id):
    cur.execute("""
        SELECT COUNT(*)
        FROM processo_pendencias
        WHERE processo_id = ?
          AND empresa_id = ?
          AND status = 'Pendente'
    """, (processo_id, empresa_id))

    pendentes = cur.fetchone()[0]

    if pendentes == 0:
        cur.execute("""
            UPDATE processos_documentais
            SET status = 'Finalizado',
                proxima_acao = 'Processo concluído'
            WHERE id = ?
              AND empresa_id = ?
        """, (processo_id, empresa_id))
    else:
        cur.execute("""
            UPDATE processos_documentais
            SET status = 'Aberto',
                proxima_acao = 'Resolver pendências abertas'
            WHERE id = ?
              AND empresa_id = ?
        """, (processo_id, empresa_id))


def atualizar_processo_por_baixa_financeira(cur, documento_id, empresa_id, tipo_baixa):
    if not documento_id:
        return

    cur.execute("""
        SELECT processo_id
        FROM processo_documentos
        WHERE documento_id = ?
          AND empresa_id = ?
    """, (documento_id, empresa_id))

    processos = cur.fetchall()

    for (processo_id,) in processos:
        if tipo_baixa == "receber":
            cur.execute("""
                UPDATE processo_pendencias
                SET status = 'Concluída'
                WHERE processo_id = ?
                  AND empresa_id = ?
                  AND status = 'Pendente'
                  AND (
                      descricao LIKE '%Recebimento%'
                      OR descricao LIKE '%recebimento%'
                      OR descricao LIKE '%bancário%'
                      OR descricao LIKE '%bancario%'
                      OR tipo_evidencia LIKE '%Extrato%'
                      OR tipo_evidencia LIKE '%Recebimento%'
                  )
            """, (processo_id, empresa_id))

        elif tipo_baixa == "pagar":
            cur.execute("""
                UPDATE processo_pendencias
                SET status = 'Concluída'
                WHERE processo_id = ?
                  AND empresa_id = ?
                  AND status = 'Pendente'
                  AND (
                      descricao LIKE '%pagamento%'
                      OR descricao LIKE '%Pagamento%'
                      OR descricao LIKE '%bancário%'
                      OR descricao LIKE '%bancario%'
                      OR tipo_evidencia LIKE '%Extrato%'
                      OR tipo_evidencia LIKE '%pagamento%'
                      OR tipo_evidencia LIKE '%Pagamento%'
                  )
            """, (processo_id, empresa_id))

        atualizar_status_processo_por_id(cur, processo_id, empresa_id)
