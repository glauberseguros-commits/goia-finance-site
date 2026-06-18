import base64
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="GOIA Finance Platform",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def moeda(valor):
    return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def carregar_logo():
    caminhos = [
        Path("assets/logo_goia.png"),
        Path("imagens/LOGO GOIA.png"),
    ]

    for caminho in caminhos:
        if caminho.exists():
            return base64.b64encode(caminho.read_bytes()).decode()

    return ""


df = pd.read_csv("dados/financeiro.csv")

recebimentos = df[df["tipo"] == "Receber"]["valor"].sum()
pagamentos = abs(df[df["tipo"] == "Pagar"]["valor"].sum())
saldo = recebimentos - pagamentos
pendencias = len(df[df["status"] == "Pendente"])

logo_base64 = carregar_logo()

st.markdown("""
<style>
[data-testid="stSidebar"],
[data-testid="collapsedControl"] {
    display: none !important;
}

[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at top right, rgba(37,99,235,.10), transparent 28%),
                linear-gradient(135deg, #f8fafc 0%, #f1f5ff 48%, #ffffff 100%);
}

.block-container {
    max-width: 1580px;
    padding-top: 1.4rem;
    padding-left: 3rem;
    padding-right: 3rem;
}

.topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 26px;
}

.top-logo {
    width: 190px;
}

.top-user {
    display: flex;
    align-items: center;
    gap: 16px;
    color: #475569;
    font-size: 14px;
}

.avatar {
    width: 42px;
    height: 42px;
    border-radius: 50%;
    background: #2563eb;
    color: white;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
}

.hero {
    display: grid;
    grid-template-columns: 1fr 300px;
    align-items: center;
    gap: 34px;
    padding: 44px 54px;
    border-radius: 28px;
    background: linear-gradient(135deg, rgba(255,255,255,.96), rgba(239,247,255,.92));
    border: 1px solid #e5e7eb;
    box-shadow: 0 22px 70px rgba(15,23,42,.08);
}

.hero-title {
    font-size: 36px;
    font-weight: 950;
    letter-spacing: -.9px;
    color: #0f172a;
    margin-bottom: 16px;
}

.hero-text {
    max-width: 820px;
    color: #475569;
    font-size: 17px;
    line-height: 1.6;
}

.wave {
    height: 150px;
    border-radius: 20px;
    background: repeating-radial-gradient(ellipse at center, rgba(14,165,233,.35) 0 1px, transparent 2px 18px);
    opacity: .45;
}

.card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 24px;
    padding: 26px;
    box-shadow: 0 18px 48px rgba(15,23,42,.07);
    min-height: 150px;
}

.kpi-label {
    color: #475569;
    font-size: 15px;
    font-weight: 800;
}

.kpi-value {
    color: #020617;
    font-size: 32px;
    font-weight: 950;
    margin-top: 8px;
}

.kpi-sub {
    color: #64748b;
    font-size: 14px;
    margin-top: 6px;
}

.kpi-trend {
    margin-top: 14px;
    font-size: 14px;
    font-weight: 800;
}

.positive { color: #16a34a; }
.negative { color: #dc2626; }
.purple { color: #7c3aed; }

.section-title {
    font-size: 24px;
    font-weight: 950;
    color: #0f172a;
    margin: 28px 0 14px;
}

.module-title {
    font-weight: 950;
    font-size: 17px;
    color: #0f172a;
    margin-bottom: 8px;
}

.module-text {
    color: #64748b;
    font-size: 14px;
    line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="topbar">
    <div>
        <img class="top-logo" src="data:image/png;base64,{logo_base64}">
    </div>
    <div class="top-user">
        <span>18 de junho de 2026</span>
        <span>🔔</span>
        <span class="avatar">GS</span>
        <span><b>Glauber</b><br><span style="font-size:12px;color:#64748b;">Administrador</span></span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div>
        <div class="hero-title">Inteligência que transforma finanças</div>
        <div class="hero-text">
        Automação financeira document-driven para importar documentos, estruturar compras e vendas,
        controlar contas a pagar e receber, acompanhar processos documentais e apoiar a conciliação bancária.
        </div>
    </div>
    <div class="wave"></div>
</div>
""", unsafe_allow_html=True)

st.write("")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="card">
        <div class="kpi-label">↗ Recebimentos</div>
        <div class="kpi-value">{moeda(recebimentos)}</div>
        <div class="kpi-sub">Total de receitas</div>
        <div class="kpi-trend positive">↑ 12,5% vs. mês anterior</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="card">
        <div class="kpi-label">↘ Pagamentos</div>
        <div class="kpi-value">{moeda(pagamentos)}</div>
        <div class="kpi-sub">Total de despesas</div>
        <div class="kpi-trend negative">↑ 8,3% vs. mês anterior</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="card">
        <div class="kpi-label">🏦 Saldo operacional</div>
        <div class="kpi-value">{moeda(saldo)}</div>
        <div class="kpi-sub">Resultado do período</div>
        <div class="kpi-trend positive">↑ 18,7% vs. mês anterior</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="card">
        <div class="kpi-label">▣ Pendências</div>
        <div class="kpi-value">{pendencias}</div>
        <div class="kpi-sub">Itens pendentes</div>
        <div class="kpi-trend purple">Ver detalhes →</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="section-title">Módulos principais</div>', unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)

with m1:
    st.markdown("""
    <div class="card">
        <div class="module-title">📄 Importar Documento</div>
        <div class="module-text">Entrada única para notas, comprovantes, boletos, extratos e documentos financeiros.</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown("""
    <div class="card">
        <div class="module-title">↻ Conciliação Bancária</div>
        <div class="module-text">Cruzamento entre movimentos bancários, contas a pagar, contas a receber e comprovantes.</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown("""
    <div class="card">
        <div class="module-title">📁 Processos Documentais</div>
        <div class="module-text">Controle de pendências, evidências e encerramento financeiro por documento.</div>
    </div>
    """, unsafe_allow_html=True)

g1, g2 = st.columns(2)

with g1:
    st.markdown('<div class="section-title">Recebimentos x Pagamentos</div>', unsafe_allow_html=True)
    grafico = df.groupby("tipo", as_index=False)["valor"].sum()
    grafico["valor"] = grafico["valor"].abs()

    fig = px.bar(
        grafico,
        x="tipo",
        y="valor",
        text="valor",
        color="tipo",
        color_discrete_map={"Receber": "#22c55e", "Pagar": "#ef4444"}
    )
    fig.update_layout(
        height=360,
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    fig.update_traces(texttemplate="R$ %{text:,.2f}", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

with g2:
    st.markdown('<div class="section-title">Status das movimentações</div>', unsafe_allow_html=True)
    fig2 = px.pie(
        df,
        names="status",
        hole=0.62,
        color_discrete_sequence=["#2563eb", "#facc15", "#ef4444", "#22c55e"]
    )
    fig2.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=10, b=10),
        legend_title_text="",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown('<div class="section-title">Movimentações financeiras</div>', unsafe_allow_html=True)

df_show = df.copy()
df_show["valor"] = df_show["valor"].apply(moeda)

st.dataframe(df_show, use_container_width=True, hide_index=True)

st.caption("GOIA Finance Platform · Versão 1.1")
