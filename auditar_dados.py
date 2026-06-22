import sqlite3

conn = sqlite3.connect("bd/gofinance.db")
cur = conn.cursor()

tabelas = [
    "empresas",
    "documentos",
    "clientes",
    "fornecedores",
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
    "conciliacoes",
    "lancamentos",
    "documentos_importados"
]

for tabela in tabelas:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {tabela}")
        qtd = cur.fetchone()[0]
        print(f"{tabela}: {qtd}")
    except Exception as e:
        print(f"{tabela}: ERRO - {e}")

conn.close()
