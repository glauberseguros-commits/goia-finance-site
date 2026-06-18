import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from pathlib import Path

DB_PATH = "bd/gofinance.db"
Path("bd").mkdir(exist_ok=True)

st.set_page_config(
    page_title="GOIA",
    page_icon="💰",
    layout="wide"
)

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def carregar_movimentacoes():
    conn = sqlite3.connect(DB_PATH)

    pagar = pd.read_sql_query("""
        SELECT data_vencimento AS data, 'Pagar' AS tipo, descricao, -valor AS valor, status, 'Compras' AS categoria
        FROM contas_pagar
        WHERE empresa_id = 1
    """, conn)

    receber = pd.read_sql_query("""
        SELECT data_vencimento AS data, 'Receber' AS tipo, descricao, valor, status, 'Vendas' AS categoria
        FROM contas_receber
        WHERE empresa_id = 1
    """, conn)

    conn.close()
    return pd.concat([pagar, receber], ignore_index=True)

df = carregar_movimentacoes()

recebimentos = df[df["tipo"] == "Receber"]["valor"].sum() if not df.empty else 0
pagamentos = abs(df[df["tipo"] == "Pagar"]["valor"].sum()) if not df.empty else 0
saldo = recebimentos - pagamentos
pendencias = len(df[df["status"] == "Pendente"]) if not df.empty else 0

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 45%, #ffffff 100%);
}
[data-testid="stSidebar"] {
    background: #0b1020;
}
[data-testid="stSidebar"] * {
    color: #e5e7eb !important;
}
.block-container {
    padding-top: 2.5rem;
    max-width: 1220px;
}
.hero {
    padding: 46px 48px;
    border-radius: 32px;
    background: radial-gradient(circle at 20% 20%, #0ea5e9 0%, transparent 26%),
                linear-gradient(135deg, #020617 0%, #172554 48%, #2563eb 100%);
    color: white;
    box-shadow: 0 28px 80px rgba(15, 23, 42, 0.32);
}
.hero-logo {
    max-width: 360px;
    margin-bottom: 28px;
}
.hero-title {
    font-size: 46px;
    line-height: 1.04;
    font-weight: 900;
    letter-spacing: -1.5px;
    color: #ffffff;
    margin-bottom: 18px;
}
.hero-text {
    font-size: 19px;
    line-height: 1.6;
    color: #dbeafe;
    max-width: 760px;
}
.metric-card {
    padding: 24px;
    background: white;
    border-radius: 24px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
}
.metric-label {
    color:#64748b;
    font-size:14px;
    font-weight:800;
}
.metric-value {
    font-size:30px;
    font-weight:900;
    color:#0f172a;
    margin-top:8px;
}
.section-title {
    font-size: 32px;
    font-weight: 900;
    color: #111827;
    letter-spacing: -1px;
    margin-top: 28px;
}
.feature-card {
    padding: 26px;
    background: white;
    border-radius: 24px;
    border: 1px solid #e5e7eb;
    min-height: 170px;
    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.07);
}
.feature-card h3 {
    font-size: 20px;
    margin-bottom: 10px;
}
.feature-card p {
    color: #64748b;
    line-height: 1.55;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero">', unsafe_allow_html=True)
st.image("assets/logo_goia.png", width=390)
st.markdown("""
<div class="hero-title">INTELIGÊNCIA QUE TRANSFORMA FINANÇAS</div>
<div class="hero-text">
Automação financeira document-driven para importar documentos, estruturar compras e vendas,
controlar contas a pagar e receber, acompanhar processos documentais e apoiar a conciliação bancária.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.write("")
st.write("")

c1, c2, c3, c4 = st.columns(4)

dados_metricas = [
    ("Recebimentos", formatar_moeda(recebimentos)),
    ("Pagamentos", formatar_moeda(pagamentos)),
    ("Saldo operacional", formatar_moeda(saldo)),
    ("Pendências", str(pendencias)),
]

for col, (titulo, valor) in zip([c1, c2, c3, c4], dados_metricas):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{titulo}</div>
            <div class="metric-value">{valor}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<div class="section-title">Módulos principais</div>', unsafe_allow_html=True)

f1, f2, f3 = st.columns(3)

with f1:
    st.markdown("""
    <div class="feature-card">
        <h3>📄 Importar Documento</h3>
        <p>Entrada única para notas, comprovantes, boletos, extratos e documentos financeiros.</p>
    </div>
    """, unsafe_allow_html=True)

with f2:
    st.markdown("""
    <div class="feature-card">
        <h3>🔄 Conciliação Bancária</h3>
        <p>Cruzamento entre movimentos bancários, contas a pagar, contas a receber e comprovantes.</p>
    </div>
    """, unsafe_allow_html=True)

with f3:
    st.markdown("""
    <div class="feature-card">
        <h3>📁 Processos Documentais</h3>
        <p>Controle de pendências, evidências e encerramento financeiro por documento.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

g1, g2 = st.columns(2)

with g1:
    st.subheader("Recebimentos x Pagamentos")
    if not df.empty:
        grafico = df.groupby("tipo", as_index=False)["valor"].sum()
        grafico["valor"] = grafico["valor"].abs()
        fig = px.bar(grafico, x="tipo", y="valor", text="valor")
        fig.update_traces(texttemplate="%{text:.2f}", textposition="inside")
        st.plotly_chart(fig, use_container_width=True)

with g2:
    st.subheader("Status das movimentações")
    if not df.empty:
        fig2 = px.pie(df, names="status", hole=0.6)
        st.plotly_chart(fig2, use_container_width=True)

st.subheader("Movimentações financeiras")

if not df.empty:
    df_show = df.copy()
    df_show["data"] = pd.to_datetime(df_show["data"], errors="coerce").dt.strftime("%d/%m/%Y")
    df_show["valor"] = df_show["valor"].apply(formatar_moeda)
    st.dataframe(df_show, width="stretch", hide_index=True)

st.caption("Versão 0.7 - GOIA Premium")
