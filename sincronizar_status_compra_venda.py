import sqlite3

conn = sqlite3.connect("bd/gofinance.db")
cur = conn.cursor()

cur.execute("""
    UPDATE compras
    SET status = 'Finalizada'
    WHERE empresa_id = 1
      AND documento_id IN (
          SELECT documento_id
          FROM contas_pagar
          WHERE empresa_id = 1
            AND status = 'Baixada'
      )
""")

cur.execute("""
    UPDATE vendas
    SET status = 'Finalizada'
    WHERE empresa_id = 1
      AND documento_id IN (
          SELECT documento_id
          FROM contas_receber
          WHERE empresa_id = 1
            AND status = 'Baixada'
      )
""")

conn.commit()

print("Compras atualizadas:", cur.rowcount)

print("\nCOMPRAS")
for x in cur.execute("""
SELECT id, documento_id, valor_total, status
FROM compras
ORDER BY id
"""):
    print(x)

print("\nVENDAS")
for x in cur.execute("""
SELECT id, documento_id, valor_total, status
FROM vendas
ORDER BY id
"""):
    print(x)

conn.close()
