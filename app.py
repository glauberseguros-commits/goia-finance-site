import base64
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from pathlib import Path

DB_PATH = "bd/gofinance.db"

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def carregar_movimentacoes():
    conn = sqlite3.connect(DB_PATH)

    pagar = pd.read_sql_query("""
        SELECT data_vencimento AS data,
               'Pagar' AS tipo,
               descricao,
               -valor AS valor,
               status,
               'Compras' AS categoria
        FROM contas_pagar
        WHERE empresa_id = 1
    """, conn)

    receber = pd.read_sql_query("""
        SELECT data_vencimento AS data,
               'Receber' AS tipo,
               descricao,
               valor,
               status,
               'Vendas' AS categoria
        FROM contas_receber
        WHERE empresa_id = 1
    """, conn)

    conn.close()

    return pd.concat([pagar, receber], ignore_index=True)

st.set_page_config(
    page_title="GOIA",
    page_icon="💰",
    layout="wide"
)

df = carregar_movimentacoes()

recebimentos = df[df["tipo"] == "Receber"]["valor"].sum() if not df.empty else 0
pagamentos = abs(df[df["tipo"] == "Pagar"]["valor"].sum()) if not df.empty else 0
saldo = recebimentos - pagamentos
pendencias = len(df[df["status"] == "Pendente"]) if not df.empty else 0

logo_base64 = base64.b64encode(
    Path("assets/logo_goia.png").read_bytes()
).decode()

st.markdown("""
<style>

[data-testid="stAppViewContainer"]{
    background:linear-gradient(135deg,#f8fafc 0%,#eef2ff 45%,#ffffff 100%);
}

[data-testid="stSidebar"]{
    background:#0b1020;
}

[data-testid="stSidebar"] *{
    color:#e5e7eb !important;
}

.block-container{
    max-width:1220px;
    padding-top:2rem;
}

.hero{
    padding:48px;
    border-radius:32px;
    background:radial-gradient(circle at 20% 20%, #0ea5e9 0%, transparent 26%),
               linear-gradient(135deg,#020617 0%,#172554 48%,#2563eb 100%);
    color:white;
    box-shadow:0 28px 80px rgba(15,23,42,.32);
}

.hero-logo{
    width:390px;
    max-width:100%;
    display:block;
    border-radius:12px;
    margin-bottom:28px;
}

.hero-title{
    font-size:46px;
    font-weight:900;
    line-height:1.05;
    color:white;
}

.hero-text{
    margin-top:18px;
    max-width:760px;
    font-size:19px;
    line-height:1.6;
    color:#dbeafe;
}

.metric-card{
    padding:24px;
    background:white;
    border-radius:24px;
    border:1px solid #e5e7eb;
    box-shadow:0 18px 45px rgba(15,23,42,.08);
}

.metric-label{
    color:#64748b;
    font-size:14px;
    font-weight:800;
}

.metric-value{
    color:#0f172a;
    font-size:30px;
    font-weight:900;
    margin-top:8px;
}

.section-title{
    font-size:32px;
    font-weight:900;
    margin-top:30px;
}

.feature-card{
    padding:26px;
    background:white;
    border-radius:24px;
    border:1px solid #e5e7eb;
    min-height:170px;
    box-shadow:0 18px 45px rgba(15,23,42,.07);
}

</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="hero">

<img src="data:image/png;base64,{logo_base64}" class="hero-logo">

<div class="hero-title">
INTELIGÊNCIA QUE TRANSFORMA FINANÇAS
</div>

<div class="hero-text">
Automação financeira document-driven para importar documentos, estruturar compras e vendas,
controlar contas a pagar e receber, acompanhar processos documentais e apoiar a conciliação bancária.
</div>

</div>
""", unsafe_allow_html=True)

st.write("")
st.write("")
st.caption("Versão 0.7 - GOIA Premium")
