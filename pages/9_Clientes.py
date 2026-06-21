import streamlit as st
from utils.ui import aplicar_estilo_premium
import pandas as pd
import sqlite3

from utils.auth import empresa_logada, exigir_login

DB_PATH = "bd/gofinance.db"

exigir_login()
EMPRESA_ID = empresa_logada()

st.set_page_config(page_title="Clientes", page_icon="👥", layout="wide")

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
    st.sidebar.page_link("pages/7_Processos_Documentais.py", label="Processos Documentais", icon="🗂️")
    st.sidebar.page_link("pages/8_Conciliacao_Bancaria.py", label="Conciliação Bancária", icon="🏦")

menu_goia()



st.title("👥 Clientes")
st.caption("Clientes identificados automaticamente a partir dos documentos importados.")

def conectar():
    return sqlite3.connect(DB_PATH)

def moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

def data_br(valor):
    if not valor:
        return ""
    try:
        return pd.to_datetime(valor).strftime("%d/%m/%Y")
    except Exception:
        return valor

conn = conectar()

clientes = pd.read_sql_query("""
SELECT
    id,
    nome,
    cnpj_cpf,
    cidade,
    uf,
    status,
    origem_cadastro
FROM clientes
WHERE empresa_id = ?
ORDER BY nome
""", conn, params=(EMPRESA_ID,))

conn.close()

st.subheader("Clientes cadastrados")

busca = st.text_input("Buscar cliente por nome ou CNPJ/CPF")

if busca and not clientes.empty:
    clientes = clientes[
        clientes["nome"].fillna("").str.contains(busca, case=False, na=False)
        | clientes["cnpj_cpf"].fillna("").str.contains(busca, case=False, na=False)
    ]

if clientes.empty:
    st.info("Nenhum cliente cadastrado. Importe documentos financeiros para o sistema classificar clientes automaticamente.")
else:
    st.dataframe(clientes.drop(columns=["id"]), width="stretch", hide_index=True)

    st.divider()
    st.subheader("Histórico financeiro do cliente")

    cliente_nome = st.selectbox("Selecionar cliente", clientes["nome"].tolist())
    cliente_id = int(clientes[clientes["nome"] == cliente_nome]["id"].iloc[0])

    conn = conectar()

    notas = pd.read_sql_query("""
    SELECT numero_nfe, serie_nfe, data_emissao, valor, status_processamento
    FROM documentos
    WHERE empresa_id = ?
      AND direcao = 'Nota Fiscal de Venda'
      AND (
          cnpj_destinatario = (SELECT cnpj_cpf FROM clientes WHERE id = ?)
          OR nome_destinatario = (SELECT nome FROM clientes WHERE id = ?)
      )
    ORDER BY data_emissao DESC
    """, conn, params=(EMPRESA_ID, cliente_id, cliente_id))

    receber = pd.read_sql_query("""
    SELECT descricao, valor, valor_baixado, data_vencimento, data_baixa, status
    FROM contas_receber
    WHERE empresa_id = ?
      AND cliente_id = ?
    ORDER BY data_vencimento DESC
    """, conn, params=(EMPRESA_ID, cliente_id))

    conn.close()

    st.markdown("### Notas fiscais emitidas")
    if notas.empty:
        st.info("Nenhuma NF-e de venda encontrada para este cliente.")
    else:
        notas["data_emissao"] = notas["data_emissao"].apply(data_br)
        notas["valor"] = notas["valor"].apply(moeda)
        st.dataframe(notas, width="stretch", hide_index=True)

    st.markdown("### Contas a receber")
    if receber.empty:
        st.info("Nenhuma conta a receber encontrada para este cliente.")
    else:
        receber["data_vencimento"] = receber["data_vencimento"].apply(data_br)
        receber["data_baixa"] = receber["data_baixa"].apply(data_br)
        receber["valor"] = receber["valor"].apply(moeda)
        receber["valor_baixado"] = receber["valor_baixado"].apply(moeda)
        st.dataframe(receber, width="stretch", hide_index=True)
