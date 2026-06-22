import sqlite3

DB = "bd/gofinance.db"
ORIGEM = 1
DESTINO = 2

tabelas = [
    "clientes",
    "fornecedores",
    "produtos",
    "documentos",
    "compras",
    "compras_itens",
    "vendas",
    "vendas_itens",
    "contas_pagar",
    "contas_receber",
    "processos_documentais",
    "processo_documentos",
    "processo_pendencias",
    "processo_evidencias",
    "movimentos_bancarios",
    "conciliacoes"
]

conn = sqlite3.connect(DB)
cur = conn.cursor()

for tabela in tabelas:
    try:
        cur.execute(f"""
            UPDATE {tabela}
            SET empresa_id = ?
            WHERE empresa_id = ?
        """, (DESTINO, ORIGEM))
        print(f"{tabela}: {cur.rowcount} registro(s) migrado(s)")
    except Exception as e:
        print(f"{tabela}: ERRO - {e}")

conn.commit()
conn.close()

print("Migração concluída.")
