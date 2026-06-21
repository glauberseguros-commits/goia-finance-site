import sqlite3

import pandas as pd
import streamlit as st
from utils.auth import empresa_logada, exigir_login
from utils.ui import aplicar_estilo_premium

DB_PATH = "bd/gofinance.db"

exigir_login()
EMPRESA_ID_ATIVA = empresa_logada()

st.set_page_config(
    page_title="Fornecedores",
    page_icon="🏭",
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

st.title("🏭 Fornecedores")
st.caption("Fornecedores identificados automaticamente a partir dos documentos importados.")


def conectar():
    return sqlite3.connect(DB_PATH)


def moeda(valor):
    try:
        return f"R$ {float(valor or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def data_br(valor):
    if not valor:
        return ""
    try:
        return pd.to_datetime(valor).strftime("%d/%m/%Y")
    except Exception:
        return str(valor)


def carregar_fornecedores():
    conn = conectar()

    query = """
        SELECT
            id,
            nome,
            cnpj,
            categoria_padrao,
            email,
            telefone,
            cidade,
            uf,
            status,
            origem_cadastro
        FROM fornecedores
        WHERE empresa_id = ?
        ORDER BY nome
    """

    df = pd.read_sql_query(query, conn, params=(EMPRESA_ID_ATIVA,))
    conn.close()
    return df


def carregar_notas_fornecedor(fornecedor_id):
    conn = conectar()

    query = """
        SELECT
            numero_nfe,
            serie_nfe,
            data_emissao,
            valor,
            status_processamento
        FROM documentos
        WHERE empresa_id = ?
          AND direcao = 'Nota Fiscal de Compra'
          AND (
              cnpj_emitente = (
                  SELECT cnpj
                  FROM fornecedores
                  WHERE id = ?
                    AND empresa_id = ?
              )
              OR nome_emitente = (
                  SELECT nome
                  FROM fornecedores
                  WHERE id = ?
                    AND empresa_id = ?
              )
          )
        ORDER BY data_emissao DESC
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(
            EMPRESA_ID_ATIVA,
            fornecedor_id,
            EMPRESA_ID_ATIVA,
            fornecedor_id,
            EMPRESA_ID_ATIVA
        )
    )

    conn.close()
    return df


def carregar_pagar_fornecedor(fornecedor_id):
    conn = conectar()

    query = """
        SELECT
            descricao,
            categoria,
            valor,
            valor_baixado,
            data_vencimento,
            data_baixa,
            status
        FROM contas_pagar
        WHERE empresa_id = ?
          AND fornecedor_id = ?
        ORDER BY data_vencimento DESC
    """

    df = pd.read_sql_query(query, conn, params=(EMPRESA_ID_ATIVA, fornecedor_id))
    conn.close()
    return df


fornecedores = carregar_fornecedores()

st.subheader("Fornecedores cadastrados")

busca = st.text_input("Buscar fornecedor por nome ou CNPJ/CPF")

if busca and not fornecedores.empty:
    fornecedores = fornecedores[
        fornecedores["nome"].fillna("").str.contains(busca, case=False, na=False)
        | fornecedores["cnpj"].fillna("").str.contains(busca, case=False, na=False)
    ]

if fornecedores.empty:
    st.info("Nenhum fornecedor cadastrado. Importe documentos financeiros para o sistema classificar fornecedores automaticamente.")
    st.stop()

fornecedores_exibicao = fornecedores.copy()

fornecedores_exibicao = fornecedores_exibicao.rename(columns={
    "nome": "Nome",
    "cnpj": "CNPJ/CPF",
    "categoria_padrao": "Categoria",
    "email": "E-mail",
    "telefone": "Telefone",
    "cidade": "Cidade",
    "uf": "UF",
    "status": "Status",
    "origem_cadastro": "Origem"
})

st.dataframe(
    fornecedores_exibicao.drop(columns=["id"]),
    width="stretch",
    hide_index=True
)


st.divider()

st.caption("Versão 0.3 - Fornecedores")
