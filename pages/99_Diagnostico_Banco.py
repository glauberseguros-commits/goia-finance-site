import pandas as pd
import streamlit as st

from utils.auth import exigir_login
from utils.db import caminho_banco, conectar_banco

st.set_page_config(
    page_title="Diagnóstico Banco",
    page_icon="🧪",
    layout="wide"
)

exigir_login()

st.title("🧪 Diagnóstico do Banco GOIA")
st.caption("Página temporária para validar dados no banco ativo do ambiente.")

st.write("Banco ativo:")
st.code(str(caminho_banco()))

tabelas = [
    "empresas",
    "documentos",
    "repositorio_documental",
    "clientes",
    "fornecedores",
    "processos_documentais",
    "processo_documentos",
    "processo_pendencias",
    "compras",
    "contas_pagar",
    "vendas",
    "contas_receber",
]

conn = conectar_banco()

for tabela in tabelas:
    st.subheader(tabela)

    try:
        total = pd.read_sql_query(f"SELECT COUNT(*) AS total FROM {tabela}", conn)
        st.write(f"Total: {int(total['total'].iloc[0])}")

        df = pd.read_sql_query(
            f"SELECT * FROM {tabela} ORDER BY id DESC LIMIT 10",
            conn
        )

        if df.empty:
            st.info("Sem registros.")
        else:
            st.dataframe(df, width="stretch", hide_index=True)

    except Exception as e:
        st.error(f"Erro ao consultar {tabela}: {e}")

conn.close()

st.warning("Página temporária. Remover após diagnóstico.")
