import sqlite3

import pandas as pd
import streamlit as st
from utils.auth import empresa_logada, exigir_login
from utils.ui import aplicar_estilo_premium

DB_PATH = "bd/gofinance.db"

exigir_login()
EMPRESA_ID_ATIVA = empresa_logada()

st.set_page_config(
    page_title="Clientes",
    page_icon="👥",
    layout="wide"
)

aplicar_estilo_premium()

st.markdown("""
<style>
[data-testid="stSidebarNav"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)


def menu_goia():
    st.sidebar.markdown("## GOIA")
    st.sidebar.page_link("app.py", label="Dashboard", icon="🏠")
    st.sidebar.page_link("pages/1_Importar_Documento.py", label="Importar Documento", icon="📄")
    st.sidebar.page_link("pages/9_Clientes.py", label="Clientes", icon="👥")
    st.sidebar.page_link("pages/10_Fornecedores.py", label="Fornecedores", icon="🏭")
    st.sidebar.page_link("pages/2_Contas_a_Receber.py", label="Contas a Receber", icon="💰")
    st.sidebar.page_link("pages/3_Contas_a_Pagar.py", label="Contas a Pagar", icon="💸")
    st.sidebar.page_link("pages/4_Compras.py", label="Compras", icon="🛒")
    st.sidebar.page_link("pages/5_Produtos_Estoque.py", label="Produtos / Estoque", icon="📦")
    st.sidebar.page_link("pages/6_Vendas.py", label="Vendas", icon="🧾")
    st.sidebar.page_link("pages/7_Processos_Documentais.py", label="Processos Documentais", icon="🗂️")
    st.sidebar.page_link("pages/8_Conciliacao_Bancaria.py", label="Conciliação Bancária", icon="🏦")


menu_goia()

st.title("👥 Clientes")
st.caption("Cadastro de clientes identificados a partir dos documentos importados.")


def conectar():
    return sqlite3.connect(DB_PATH)


def carregar_clientes():
    conn = conectar()

    query = """
        SELECT
            id,
            nome,
            cnpj_cpf,
            email,
            telefone,
            cidade,
            uf,
            status
        FROM clientes
        WHERE empresa_id = ?
        ORDER BY nome
    """

    df = pd.read_sql_query(query, conn, params=(EMPRESA_ID_ATIVA,))
    conn.close()
    return df


clientes = carregar_clientes()

st.subheader("Clientes cadastrados")

busca = st.text_input("Buscar cliente por nome ou CPF/CNPJ")

if busca and not clientes.empty:
    clientes = clientes[
        clientes["nome"].fillna("").str.contains(busca, case=False, na=False)
        | clientes["cnpj_cpf"].fillna("").str.contains(busca, case=False, na=False)
    ]

if clientes.empty:
    st.info("Nenhum cliente cadastrado.")
    st.stop()

clientes_exibicao = clientes.rename(columns={
    "id": "ID",
    "nome": "Nome",
    "cnpj_cpf": "CPF/CNPJ",
    "email": "E-mail",
    "telefone": "Telefone",
    "cidade": "Cidade",
    "uf": "UF",
    "status": "Status"
})

st.dataframe(
    clientes_exibicao,
    width="stretch",
    hide_index=True
)

st.divider()
st.caption("Versão 0.4 - Clientes")
