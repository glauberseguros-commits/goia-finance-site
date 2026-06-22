
import sqlite3
import pandas as pd
import streamlit as st

from utils.ui import aplicar_estilo_premium, moeda
from utils.premium import aplicar_premium_goia, hero

DB = "bd/gofinance.db"
EMPRESA_ID_ATIVA = 2

st.set_page_config(
    page_title="Movimentos Bancarios",
    page_icon="GOIA",
    layout="wide"
)

aplicar_estilo_premium()
aplicar_premium_goia()

with st.sidebar:
    st.markdown("### GOIA")
    st.page_link("app.py", label="Dashboard", icon="🏠")
    st.page_link("pages/1_Importar_Documento.py", label="Importar Documento", icon="📄")
    st.page_link("pages/9_Clientes.py", label="Clientes", icon="👥")
    st.page_link("pages/10_Fornecedores.py", label="Fornecedores", icon="🏭")
    st.page_link("pages/2_Contas_a_Receber.py", label="Contas a Receber", icon="💰")
    st.page_link("pages/3_Contas_a_Pagar.py", label="Contas a Pagar", icon="💸")
    st.page_link("pages/8_Movimentos_Bancarios.py", label="Movimentos Bancários", icon="🏦")
    st.page_link("pages/8_Conciliacao_Bancaria.py", label="Conciliação Bancária", icon="⚖️")

def conectar():
    return sqlite3.connect(DB)

def carregar_movimentos():
    conn = conectar()

    query = """
        SELECT
            mb.id,
            mb.data_movimento,
            mb.historico,
            mb.valor,
            mb.tipo,
            CASE
                WHEN IFNULL(mb.conciliado, 0) = 1 THEN 'Sim'
                ELSE 'Não'
            END AS conciliado,
            mb.nome_origem,
            eb.nome_arquivo AS extrato,
            mb.criado_em
        FROM movimentos_bancarios mb
        LEFT JOIN extratos_bancarios eb
            ON eb.id = mb.extrato_id
        WHERE mb.empresa_id = ?
        ORDER BY
            mb.data_movimento DESC,
            mb.id DESC
    """

    df = pd.read_sql_query(query, conn, params=(EMPRESA_ID_ATIVA,))
    conn.close()
    return df

hero(
    "Movimentos Bancarios",
    "Central de auditoria financeira para extratos OFX, conciliacao bancaria e rastreabilidade de movimentacoes.",
    icone="GOIA"
)

df = carregar_movimentos()

if df.empty:
    st.warning("Nenhum movimento bancário encontrado. Importe um arquivo OFX em Importar Documento.")
    st.stop()

df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)

total_creditos = df.loc[df["valor"] > 0, "valor"].sum()
total_debitos = df.loc[df["valor"] < 0, "valor"].sum()
saldo = df["valor"].sum()
nao_conciliados = len(df[df["conciliado"] == "Não"])

c1, c2, c3, c4 = st.columns(4)

c1.metric("Créditos", moeda(total_creditos))
c2.metric("Débitos", moeda(abs(total_debitos)))
c3.metric("Saldo Movimentado", moeda(saldo))
c4.metric("Não Conciliados", nao_conciliados)

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    filtro_tipo = st.selectbox(
        "Tipo",
        ["Todos", "Credito", "Debito"]
    )

with col2:
    filtro_conciliado = st.selectbox(
        "Conciliação",
        ["Todos", "Sim", "Não"]
    )

with col3:
    busca = st.text_input("Buscar no histórico")

df_filtrado = df.copy()

if filtro_tipo != "Todos":
    df_filtrado = df_filtrado[df_filtrado["tipo"] == filtro_tipo]

if filtro_conciliado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["conciliado"] == filtro_conciliado]

if busca:
    termo = busca.lower().strip()
    df_filtrado = df_filtrado[
        df_filtrado["historico"].fillna("").str.lower().str.contains(termo)
        | df_filtrado["nome_origem"].fillna("").str.lower().str.contains(termo)
        | df_filtrado["extrato"].fillna("").str.lower().str.contains(termo)
    ]

df_exibicao = df_filtrado.copy()

df_exibicao["valor"] = df_exibicao["valor"].apply(moeda)

df_exibicao = df_exibicao.rename(columns={
    "id": "ID",
    "data_movimento": "Data",
    "historico": "Histórico",
    "valor": "Valor",
    "tipo": "Tipo",
    "conciliado": "Conciliado",
    "nome_origem": "Origem",
    "extrato": "Extrato",
    "criado_em": "Criado em",
})

st.dataframe(
    df_exibicao,
    use_container_width=True,
    hide_index=True
)

with st.expander("Diagnóstico técnico"):
    st.write(f"Total carregado: {len(df)}")
    st.write(f"Total filtrado: {len(df_filtrado)}")
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
