import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="GO Finance AI",
    page_icon="💰",
    layout="wide"
)

# =========================
# FUNÇÕES
# =========================

def moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =========================
# LEITURA DOS DADOS
# =========================

df = pd.read_csv("dados/financeiro.csv")
df["data"] = pd.to_datetime(df["data"])

recebimentos = df[df["tipo"] == "Receber"]["valor"].sum()
pagamentos = abs(df[df["tipo"] == "Pagar"]["valor"].sum())
saldo = recebimentos - pagamentos
pendencias = len(df[df["status"] == "Pendente"])

# =========================
# TELA
# =========================

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

# =========================
# GRÁFICOS
# =========================

col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.subheader("Recebimentos x Pagamentos")
    resumo_tipo = df.groupby("tipo")["valor"].sum().reset_index()
    resumo_tipo["valor"] = resumo_tipo["valor"].abs()
    st.bar_chart(resumo_tipo, x="tipo", y="valor")

with col_graf2:
    st.subheader("Status das Movimentações")
    resumo_status = df["status"].value_counts().reset_index()
    resumo_status.columns = ["status", "quantidade"]
    st.bar_chart(resumo_status, x="status", y="quantidade")

st.divider()

# =========================
# FILTROS
# =========================

st.subheader("Movimentações Financeiras")

col_f1, col_f2 = st.columns(2)

with col_f1:
    filtro_tipo = st.selectbox(
        "Filtrar por tipo",
        ["Todos"] + sorted(df["tipo"].unique().tolist())
    )

with col_f2:
    filtro_status = st.selectbox(
        "Filtrar por status",
        ["Todos"] + sorted(df["status"].unique().tolist())
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
    use_container_width=True,
    hide_index=True
)

st.caption("Versão 0.3")
