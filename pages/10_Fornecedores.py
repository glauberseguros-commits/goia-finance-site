import streamlit as st
from utils.ui import aplicar_estilo_premium
import pandas as pd
import sqlite3

from utils.auth import empresa_logada, exigir_login

DB_PATH = "bd/gofinance.db"

exigir_login()
EMPRESA_ID = empresa_logada()

st.set_page_config(page_title="Fornecedores", page_icon="🏭", layout="wide")

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



st.title("🏭 Fornecedores")
st.caption("Fornecedores identificados automaticamente a partir dos documentos importados.")

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

fornecedores = pd.read_sql_query("""
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
""", conn, params=(EMPRESA_ID,))

conn.close()

st.subheader("Fornecedores cadastrados")

busca = st.text_input("Buscar fornecedor por nome ou CNPJ/CPF")

if busca and not fornecedores.empty:
    fornecedores = fornecedores[
        fornecedores["nome"].fillna("").str.contains(busca, case=False, na=False)
        | fornecedores["cnpj"].fillna("").str.contains(busca, case=False, na=False)
    ]

if fornecedores.empty:
    st.info("Nenhum fornecedor cadastrado. Importe documentos financeiros para o sistema classificar fornecedores automaticamente.")
else:
    st.dataframe(fornecedores.drop(columns=["id"]), width="stretch", hide_index=True)

    st.divider()
    st.subheader("Histórico financeiro do fornecedor")

    fornecedor_nome = st.selectbox("Selecionar fornecedor", fornecedores["nome"].tolist())
    fornecedor_id = int(fornecedores[fornecedores["nome"] == fornecedor_nome]["id"].iloc[0])

    conn = conectar()

    notas = pd.read_sql_query("""
    SELECT numero_nfe, serie_nfe, data_emissao, valor, status_processamento
    FROM documentos
    WHERE empresa_id = ?
      AND direcao = 'Nota Fiscal de Compra'
      AND (
          cnpj_emitente = (SELECT cnpj FROM fornecedores WHERE id = ?)
          OR nome_emitente = (SELECT nome FROM fornecedores WHERE id = ?)
      )
    ORDER BY data_emissao DESC
    """, conn, params=(EMPRESA_ID, fornecedor_id, fornecedor_id))

    pagar = pd.read_sql_query("""
    SELECT descricao, categoria, valor, valor_baixado, data_vencimento, data_baixa, status
    FROM contas_pagar
    WHERE empresa_id = ?
      AND fornecedor_id = ?
    ORDER BY data_vencimento DESC
    """, conn, params=(EMPRESA_ID, fornecedor_id))

    conn.close()

    c1, c2, c3 = st.columns(3)
    c1.metric("Notas recebidas", moeda(notas["valor"].sum() if not notas.empty else 0))
    c2.metric("Total a pagar", moeda(pagar["valor"].sum() if not pagar.empty else 0))
    c3.metric("Total pago/baixado", moeda(pagar["valor_baixado"].sum() if not pagar.empty else 0))

    st.markdown("### Notas fiscais recebidas")
    if notas.empty:
        st.info("Nenhuma NF-e de compra encontrada para este fornecedor.")
    else:
        notas["data_emissao"] = notas["data_emissao"].apply(data_br)
        notas["valor"] = notas["valor"].apply(moeda)
        st.dataframe(notas, width="stretch", hide_index=True)

    st.markdown("### Contas a pagar")
    if pagar.empty:
        st.info("Nenhuma conta a pagar encontrada para este fornecedor.")
    else:
        pagar["data_vencimento"] = pagar["data_vencimento"].apply(data_br)
        pagar["data_baixa"] = pagar["data_baixa"].apply(data_br)
        pagar["valor"] = pagar["valor"].apply(moeda)
        pagar["valor_baixado"] = pagar["valor_baixado"].apply(moeda)
        st.dataframe(pagar, width="stretch", hide_index=True)
