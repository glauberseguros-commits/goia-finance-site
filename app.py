import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

DB_PATH = "bd/gofinance.db"
EMPRESA_ID_ATIVA = 1

st.set_page_config(
    page_title="GO Finance AI",
    page_icon="💰",
    layout="wide"
)

def moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def carregar_movimentacoes():
    conn = sqlite3.connect(DB_PATH)

    contas_pagar = pd.read_sql_query("""
        SELECT
            data_vencimento AS data,
            'Pagar' AS tipo,
            descricao,
            -ABS(valor) AS valor,
            status,
            categoria
        FROM contas_pagar
        WHERE empresa_id = ?
    """, conn, params=(EMPRESA_ID_ATIVA,))

    contas_receber = pd.read_sql_query("""
        SELECT
            data_vencimento AS data,
            'Receber' AS tipo,
            descricao,
            ABS(valor) AS valor,
            status,
            categoria
        FROM contas_receber
        WHERE empresa_id = ?
    """, conn, params=(EMPRESA_ID_ATIVA,))

    conn.close()

    df = pd.concat([contas_receber, contas_pagar], ignore_index=True)

    if df.empty:
        return pd.DataFrame(columns=["data", "tipo", "descricao", "valor", "status", "categoria"])

    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df = df.sort_values(by=["data", "tipo"], ascending=[True, True])

    return df

df = carregar_movimentacoes()

recebimentos = df[df["tipo"] == "Receber"]["valor"].sum() if not df.empty else 0
pagamentos = abs(df[df["tipo"] == "Pagar"]["valor"].sum()) if not df.empty else 0
saldo = recebimentos - pagamentos
pendencias = len(df[df["status"] == "Pendente"]) if not df.empty else 0

st.title("💰 GO Finance AI")
st.caption("Automação Financeira Inteligente | Contas a Receber • Contas a Pagar • Conciliação • Gestão")

st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Recebimentos", moeda(recebimentos))

with col2:
    st.metric("Pagamentos", moeda(pagamentos))

with col3:
    st.metric("Saldo", moeda(saldo))

with col4:
    st.metric("Pendências", pendencias)

st.divider()

if df.empty:
    st.info("Nenhuma movimentação financeira cadastrada ainda.")
    st.caption("Versão 0.4")
    st.stop()

col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.subheader("Recebimentos x Pagamentos")
    resumo_tipo = df.groupby("tipo")["valor"].sum().reset_index()
    resumo_tipo["valor"] = resumo_tipo["valor"].abs()

    fig1 = px.bar(
        resumo_tipo,
        x="tipo",
        y="valor",
        text="valor",
        title=""
    )

    fig1.update_layout(height=300)

    st.plotly_chart(fig1, width="stretch")

with col_graf2:
    st.subheader("Status das Movimentações")
    resumo_status = df["status"].value_counts().reset_index()
    resumo_status.columns = ["status", "quantidade"]

    fig2 = px.pie(
        resumo_status,
        names="status",
        values="quantidade",
        hole=0.5
    )

    fig2.update_layout(height=300)

    st.plotly_chart(fig2, width="stretch")

st.divider()

st.subheader("Movimentações Financeiras")

col_f1, col_f2 = st.columns(2)

with col_f1:
    filtro_tipo = st.selectbox(
        "Filtrar por tipo",
        ["Todos"] + sorted(df["tipo"].dropna().unique().tolist())
    )

with col_f2:
    filtro_status = st.selectbox(
        "Filtrar por status",
        ["Todos"] + sorted(df["status"].dropna().unique().tolist())
    )

df_filtrado = df.copy()

if filtro_tipo != "Todos":
    df_filtrado = df_filtrado[df_filtrado["tipo"] == filtro_tipo]

if filtro_status != "Todos":
    df_filtrado = df_filtrado[df_filtrado["status"] == filtro_status]

df_exibicao = df_filtrado.copy()
df_exibicao["data"] = df_exibicao["data"].dt.strftime("%d/%m/%Y")
df_exibicao["valor"] = df_exibicao["valor"].apply(moeda)

st.dataframe(
    df_exibicao,
    width="stretch",
    hide_index=True
)

st.caption("Versão 0.4")
