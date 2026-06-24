import pandas as pd
import streamlit as st

from utils.auth import exigir_login
from utils.db import conectar_banco

st.set_page_config(layout="wide")

exigir_login()

st.title("🔍 Auditoria Pós-Importação")

conn = conectar_banco()

tabelas = [
    "documentos",
    "repositorio_documental",
    "clientes",
    "fornecedores",
    "compras",
    "vendas",
    "contas_pagar",
    "contas_receber"
]

for tabela in tabelas:
    st.header(tabela)

    try:
        total = pd.read_sql_query(
            f"SELECT COUNT(*) total FROM {tabela}",
            conn
        )

        st.write("Total:", int(total.iloc[0]["total"]))

        df = pd.read_sql_query(
            f"SELECT * FROM {tabela} ORDER BY id DESC LIMIT 20",
            conn
        )

        st.dataframe(df, width="stretch")

    except Exception as e:
        st.error(str(e))

conn.close()
