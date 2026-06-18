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

    contas_pagar = pd.read_sql_query("""
        SELECT data_vencimento AS data, 'Pagar' AS tipo, descricao, -valor AS valor, status, 'Compras' AS categoria
        FROM contas_pagar
        WHERE empresa_id = 1
    """, conn)

    contas_receber = pd.read_sql_query("""
        SELECT data_vencimento AS data, 'Receber' AS tipo, descricao, valor, status, 'Vendas' AS categoria
        FROM contas_receber
        WHERE empresa_id = 1
    """, conn)

    conn.close()

    return pd.concat([contas_pagar, contas_receber], ignore_index=True)

df = carregar_movimentacoes()

recebimentos = df[df["tipo"] == "Receber"]["valor"].sum() if not df.empty else 0
pagamentos = abs(df[df["tipo"] == "Pagar"]["valor"].sum()) if not df.empty else 0
saldo = recebimentos - pagamentos
pendencias = len(df[df["status"] == "Pendente"]) if not df.empty else 0

st.markdown("""
<style>
.main-title {
    font-size: 54px;
    font-weight: 800;
    line-height: 1.05;
    color: #111827;
}
.subtitle {
    font-size: 19px;
    color: #4b5563;
    margin-top: 16px;
    max-width: 760px;
}
.badge {
    display: inline-block;
    padding: 8px 14px;
    border-radius: 999px;
    background: #eef2ff;
    color: #3730a3;
    font-weight: 700;
    font-size: 13px;
    margin-bottom: 18px;
}
.card {
    padding: 22px;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    background: #ffffff;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
    min-height: 130px;
}
.card h3 {
    margin: 0 0 8px 0;
    font-size: 18px;
    color: #111827;
}
.card p {
    color: #6b7280;
    font-size: 14px;
}
.section-title {
    font-size: 30px;
    font-weight: 800;
    margin-top: 28px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="badge">Automação financeira inteligente</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">GO Finance AI</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Plataforma para importar documentos, estruturar compras e vendas, controlar contas a pagar e receber, acompanhar processos documentais e apoiar a conciliação bancária.</div>',
    unsafe_allow_html=True
)

st.divider()

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Recebimentos", formatar_moeda(recebimentos))

with c2:
    st.metric("Pagamentos", formatar_moeda(pagamentos))

with c3:
    st.metric("Saldo", formatar_moeda(saldo))

with c4:
    st.metric("Pendências", pendencias)

st.divider()

st.markdown('<div class="section-title">Módulos principais</div>', unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)

with m1:
    st.markdown('<div class="card"><h3>📄 Importar Documento</h3><p>Entrada única para notas, comprovantes, extratos, boletos e documentos financeiros.</p></div>', unsafe_allow_html=True)

with m2:
    st.markdown('<div class="card"><h3>🔄 Conciliação Bancária</h3><p>Cruzamento entre movimentos bancários, contas a pagar e contas a receber.</p></div>', unsafe_allow_html=True)

with m3:
    st.markdown('<div class="card"><h3>📁 Processos Documentais</h3><p>Controle de pendências, evidências e encerramento financeiro por documento.</p></div>', unsafe_allow_html=True)

st.divider()

col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("Recebimentos x Pagamentos")
    if not df.empty:
        grafico = df.groupby("tipo", as_index=False)["valor"].sum()
        grafico["valor"] = grafico["valor"].abs()
        fig = px.bar(grafico, x="tipo", y="valor", text="valor")
        fig.update_traces(texttemplate="%{text:.2f}", textposition="inside")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados financeiros.")

with col_g2:
    st.subheader("Status das Movimentações")
    if not df.empty:
        fig2 = px.pie(df, names="status", hole=0.55)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Sem dados para status.")

st.divider()

st.subheader("Movimentações Financeiras")

if df.empty:
    st.info("Nenhuma movimentação cadastrada.")
else:
    df_show = df.copy()
    df_show["data"] = pd.to_datetime(df_show["data"], errors="coerce").dt.strftime("%d/%m/%Y")
    df_show["valor"] = df_show["valor"].apply(formatar_moeda)
    st.dataframe(df_show, width="stretch", hide_index=True)

st.caption("Versão 0.5 - Landing Premium")
