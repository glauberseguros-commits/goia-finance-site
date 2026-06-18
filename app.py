import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from pathlib import Path

DB_PATH = "bd/gofinance.db"
Path("bd").mkdir(exist_ok=True)

st.set_page_config(
    page_title="GO Finance AI",
    page_icon="💰",
    layout="wide"
)

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def carregar_movimentacoes():
    conn = sqlite3.connect(DB_PATH)
    pagar = pd.read_sql_query("""
        SELECT data_vencimento AS data, 'Pagar' AS tipo, descricao, -valor AS valor, status, 'Compras' AS categoria
        FROM contas_pagar WHERE empresa_id = 1
    """, conn)
    receber = pd.read_sql_query("""
        SELECT data_vencimento AS data, 'Receber' AS tipo, descricao, valor, status, 'Vendas' AS categoria
        FROM contas_receber WHERE empresa_id = 1
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
    background: #0f172a;
}
[data-testid="stSidebar"] * {
    color: #e5e7eb !important;
}
.block-container {
    padding-top: 3rem;
    max-width: 1220px;
}
.hero {
    padding: 46px 44px;
    border-radius: 30px;
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 55%, #2563eb 100%);
    color: white;
    box-shadow: 0 26px 70px rgba(15, 23, 42, 0.28);
}
.badge {
    display: inline-block;
    background: rgba(255,255,255,.14);
    border: 1px solid rgba(255,255,255,.22);
    color: #dbeafe;
    padding: 9px 15px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 800;
    margin-bottom: 18px;
}
.hero h1 {
    font-size: 58px;
    line-height: 1.02;
    margin: 0 0 18px 0;
    letter-spacing: -2px;
}
.hero p {
    font-size: 20px;
    line-height: 1.55;
    max-width: 760px;
    color: #dbeafe;
}
.cta {
    display: inline-block;
    margin-top: 22px;
    padding: 14px 22px;
    border-radius: 14px;
    background: white;
    color: #0f172a !important;
    font-weight: 900;
}
.metric-card {
    padding: 22px;
    background: white;
    border-radius: 22px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 14px 35px rgba(15, 23, 42, 0.08);
}
.section-title {
    font-size: 32px;
    font-weight: 900;
    color: #111827;
    letter-spacing: -1px;
}
.feature-card {
    padding: 26px;
    background: white;
    border-radius: 24px;
    border: 1px solid #e5e7eb;
    min-height: 190px;
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

st.markdown("""
<div class="hero">
    <div class="badge">GOIA • Gestão financeira document-driven</div>
    <h1>Automação financeira com inteligência documental.</h1>
    <p>
        O GO Finance AI transforma documentos financeiros em contas, movimentos, processos e conciliações.
        Uma entrada única para notas, comprovantes, boletos e extratos.
    </p>
    <div class="cta">Acessar demonstração operacional</div>
</div>
""", unsafe_allow_html=True)

st.write("")
st.write("")

c1, c2, c3, c4 = st.columns(4)
for col, titulo, valor in [
    (c1, "Recebimentos", formatar_moeda(recebimentos)),
    (c2, "Pagamentos", formatar_moeda(pagamentos)),
    (c3, "Saldo operacional", formatar_moeda(saldo)),
    (c4, "Pendências", str(pendencias)),
]:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div style="color:#64748b;font-size:14px;font-weight:700;">{titulo}</div>
            <div style="font-size:30px;font-weight:900;color:#0f172a;margin-top:8px;">{valor}</div>
        </div>
        """, unsafe_allow_html=True)

st.write("")
st.write("")

st.markdown('<div class="section-title">O que a plataforma entrega</div>', unsafe_allow_html=True)

f1, f2, f3 = st.columns(3)

with f1:
    st.markdown("""
    <div class="feature-card">
        <h3>📄 Importação única</h3>
        <p>O usuário envia documentos financeiros em um único ponto. O sistema identifica, classifica e direciona para o fluxo correto.</p>
    </div>
    """, unsafe_allow_html=True)

with f2:
    st.markdown("""
    <div class="feature-card">
        <h3>🔄 Conciliação bancária</h3>
        <p>Cruzamento entre extratos, contas a pagar, contas a receber e comprovantes para reduzir baixa manual.</p>
    </div>
    """, unsafe_allow_html=True)

with f3:
    st.markdown("""
    <div class="feature-card">
        <h3>📁 Processo documental</h3>
        <p>Cada operação mantém documentos, pendências, evidências e status financeiro rastreáveis.</p>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.write("")

g1, g2 = st.columns(2)

with g1:
    st.subheader("Recebimentos x Pagamentos")
    grafico = df.groupby("tipo", as_index=False)["valor"].sum()
    grafico["valor"] = grafico["valor"].abs()
    fig = px.bar(grafico, x="tipo", y="valor", text="valor")
    fig.update_traces(texttemplate="%{text:.2f}", textposition="inside")
    st.plotly_chart(fig, use_container_width=True)

with g2:
    st.subheader("Status das movimentações")
    fig2 = px.pie(df, names="status", hole=0.6)
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Movimentações financeiras")
df_show = df.copy()
df_show["data"] = pd.to_datetime(df_show["data"], errors="coerce").dt.strftime("%d/%m/%Y")
df_show["valor"] = df_show["valor"].apply(formatar_moeda)
st.dataframe(df_show, width="stretch", hide_index=True)

st.caption("Versão 0.6 - Landing Comercial Premium")
