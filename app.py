import base64
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


DB_PATH = "bd/gofinance.db"

st.set_page_config(
    page_title="GOIA Finance Platform",
    page_icon="💰",
    layout="wide"
)


def formatar_moeda(valor):
    valor = float(valor or 0)
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def carregar_movimentacoes():
    conn = sqlite3.connect(DB_PATH)

    pagar = pd.read_sql_query("""
        SELECT
            data_vencimento AS data,
            'Pagar' AS tipo,
            descricao,
            -valor AS valor,
            status,
            'Compras' AS categoria
        FROM contas_pagar
        WHERE empresa_id = 1
    """, conn)

    receber = pd.read_sql_query("""
        SELECT
            data_vencimento AS data,
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


def carregar_logo_base64():
    svg = Path("assets/logo_goia.svg")
    png = Path("assets/logo_goia.png")

    if svg.exists():
        return "image/svg+xml", base64.b64encode(svg.read_bytes()).decode()

    if png.exists():
        return "image/png", base64.b64encode(png.read_bytes()).decode()

    return None, ""


df = carregar_movimentacoes()

recebimentos = df[df["tipo"] == "Receber"]["valor"].sum() if not df.empty else 0
pagamentos = abs(df[df["tipo"] == "Pagar"]["valor"].sum()) if not df.empty else 0
saldo = recebimentos - pagamentos
pendencias = len(df[df["status"] == "Pendente"]) if not df.empty else 0
total_mov = len(df) if not df.empty else 0

logo_mime, logo_base64 = carregar_logo_base64()
logo_html = ""
if logo_base64:
    logo_html = f'<img class="goia-logo" src="data:{logo_mime};base64,{logo_base64}">'


st.markdown("""
<style>
:root {
    --navy:#081226;
    --navy2:#0d1b3d;
    --text:#0f172a;
    --muted:#64748b;
    --line:#e5e7eb;
    --blue:#2563eb;
    --green:#10b981;
    --red:#ef4444;
    --purple:#7c3aed;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at top right, rgba(37,99,235,.10), transparent 26%),
        linear-gradient(135deg, #f8fafc 0%, #f1f5ff 48%, #ffffff 100%);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #071126 0%, #0b1733 58%, #050b18 100%);
    border-right: 1px solid rgba(255,255,255,.08);
}

[data-testid="stSidebar"] * {
    color: #e5e7eb !important;
}

.block-container {
    max-width: 1400px;
    padding-top: 1.4rem;
    padding-bottom: 3rem;
}

.topbar {
    display:flex;
    justify-content:flex-end;
    align-items:center;
    gap:18px;
    margin-bottom:22px;
    color:#475569;
    font-size:14px;
}

.avatar {
    width:40px;
    height:40px;
    border-radius:50%;
    display:inline-flex;
    align-items:center;
    justify-content:center;
    background:linear-gradient(135deg,#2563eb,#1d4ed8);
    color:white;
    font-weight:800;
}

.hero {
    display:grid;
    grid-template-columns: 260px 1fr 260px;
    align-items:center;
    gap:34px;
    padding:34px 42px;
    border-radius:26px;
    background:
        radial-gradient(circle at 94% 50%, rgba(14,165,233,.18), transparent 25%),
        linear-gradient(135deg, rgba(255,255,255,.94), rgba(240,247,255,.92));
    border:1px solid rgba(226,232,240,.95);
    box-shadow:0 22px 70px rgba(15,23,42,.08);
}

.goia-logo {
    width:240px;
    max-width:100%;
    display:block;
}

.hero h1 {
    margin:0 0 10px 0;
    font-size:30px;
    line-height:1.1;
    letter-spacing:-.8px;
    color:var(--text);
    font-weight:900;
}

.hero p {
    margin:0;
    max-width:760px;
    color:#475569;
    font-size:15.5px;
    line-height:1.55;
}

.wave {
    height:120px;
    border-radius:20px;
    opacity:.55;
    background:
        repeating-radial-gradient(ellipse at center, rgba(14,165,233,.38) 0 1px, transparent 2px 18px);
    mask-image: linear-gradient(90deg, transparent, black 20%, black 80%, transparent);
}

.kpi-grid {
    display:grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap:16px;
    margin-top:20px;
}

.kpi {
    display:flex;
    gap:18px;
    align-items:flex-start;
    padding:24px 24px;
    border-radius:24px;
    background:rgba(255,255,255,.96);
    border:1px solid var(--line);
    box-shadow:0 18px 48px rgba(15,23,42,.07);
}

.icon {
    width:52px;
    height:52px;
    min-width:52px;
    border-radius:50%;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:24px;
}

.icon.green { background:#dcfce7; color:#16a34a; }
.icon.red { background:#fee2e2; color:#dc2626; }
.icon.blue { background:#dbeafe; color:#2563eb; }
.icon.purple { background:#ede9fe; color:#7c3aed; }

.kpi-label {
    color:#475569;
    font-size:14px;
    font-weight:800;
    margin-bottom:6px;
}

.kpi-value {
    color:#020617;
    font-size:28px;
    font-weight:950;
    letter-spacing:-.5px;
}

.kpi-sub {
    color:#64748b;
    font-size:13px;
    margin-top:4px;
}

.kpi-trend {
    font-size:13px;
    margin-top:12px;
    font-weight:700;
}

.positive { color:#16a34a; }
.negative { color:#dc2626; }
.linklike { color:#7c3aed; }

.section-title {
    margin:24px 0 12px 0;
    color:#0f172a;
    font-size:22px;
    font-weight:900;
    letter-spacing:-.4px;
}

.module-grid {
    display:grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap:16px;
}

.module-card {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:18px;
    padding:22px 24px;
    min-height:106px;
    border-radius:22px;
    background:rgba(255,255,255,.96);
    border:1px solid var(--line);
    box-shadow:0 16px 42px rgba(15,23,42,.06);
}

.module-left {
    display:flex;
    align-items:center;
    gap:18px;
}

.module-title {
    font-weight:900;
    color:#0f172a;
    margin-bottom:6px;
}

.module-text {
    color:#64748b;
    font-size:13.5px;
    line-height:1.45;
}

.arrow {
    color:#334155;
    font-size:24px;
}

.chart-grid {
    display:grid;
    grid-template-columns: 1fr 1fr;
    gap:16px;
    margin-top:16px;
}

.panel {
    padding:22px;
    border-radius:24px;
    background:rgba(255,255,255,.96);
    border:1px solid var(--line);
    box-shadow:0 18px 48px rgba(15,23,42,.07);
}

.panel-title {
    font-size:18px;
    font-weight:900;
    color:#0f172a;
    margin-bottom:10px;
}

.sidebar-brand {
    padding:22px 10px 26px 10px;
}

.sidebar-brand img {
    width:150px;
    max-width:100%;
}

.sidebar-card {
    margin-top:28px;
    padding:20px;
    border-radius:20px;
    border:1px solid rgba(96,165,250,.25);
    background:rgba(37,99,235,.10);
}

.sidebar-card-title {
    font-weight:900;
    margin-top:12px;
}

.sidebar-card-text {
    color:#cbd5e1 !important;
    font-size:13px;
    line-height:1.45;
    margin-top:8px;
}

@media (max-width: 1100px) {
    .hero {
        grid-template-columns: 1fr;
    }
    .wave {
        display:none;
    }
    .kpi-grid, .module-grid, .chart-grid {
        grid-template-columns: 1fr;
    }
}
</style>
""", unsafe_allow_html=True)


with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-brand">
        {logo_html}
    </div>
    <div class="sidebar-card">
        <div style="font-size:26px;">✦</div>
        <div class="sidebar-card-title">GOIA Finance Platform</div>
        <div class="sidebar-card-text">
            Automação financeira document-driven para empresas que precisam de controle, evidência e conciliação.
        </div>
    </div>
    """, unsafe_allow_html=True)


st.markdown("""
<div class="topbar">
    <span>📅 18 de junho de 2026</span>
    <span>🔔</span>
    <span class="avatar">GS</span>
    <span><b>Glauber</b><br><span style="font-size:12px;color:#64748b;">Administrador</span></span>
</div>
""", unsafe_allow_html=True)


st.markdown(f"""
<div class="hero">
    <div>{logo_html}</div>
    <div>
        <h1>Inteligência que transforma finanças</h1>
        <p>
            Automação financeira document-driven para importar documentos, estruturar compras e vendas,
            controlar contas a pagar e receber, acompanhar processos documentais e apoiar a conciliação bancária.
        </p>
    </div>
    <div class="wave"></div>
</div>
""", unsafe_allow_html=True)


st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi">
        <div class="icon green">↗</div>
        <div>
            <div class="kpi-label">Recebimentos</div>
            <div class="kpi-value">{formatar_moeda(recebimentos)}</div>
            <div class="kpi-sub">Total de receitas</div>
            <div class="kpi-trend positive">↑ 12,5% vs. mês anterior</div>
        </div>
    </div>

    <div class="kpi">
        <div class="icon red">↘</div>
        <div>
            <div class="kpi-label">Pagamentos</div>
            <div class="kpi-value">{formatar_moeda(pagamentos)}</div>
            <div class="kpi-sub">Total de despesas</div>
            <div class="kpi-trend negative">↑ 8,3% vs. mês anterior</div>
        </div>
    </div>

    <div class="kpi">
        <div class="icon blue">🏦</div>
        <div>
            <div class="kpi-label">Saldo operacional</div>
            <div class="kpi-value">{formatar_moeda(saldo)}</div>
            <div class="kpi-sub">Resultado do período</div>
            <div class="kpi-trend positive">↑ 18,7% vs. mês anterior</div>
        </div>
    </div>

    <div class="kpi">
        <div class="icon purple">▣</div>
        <div>
            <div class="kpi-label">Pendências</div>
            <div class="kpi-value">{pendencias}</div>
            <div class="kpi-sub">Itens pendentes</div>
            <div class="kpi-trend linklike">Ver detalhes →</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


st.markdown('<div class="section-title">Módulos principais</div>', unsafe_allow_html=True)

st.markdown("""
<div class="module-grid">
    <div class="module-card">
        <div class="module-left">
            <div class="icon blue">📄</div>
            <div>
                <div class="module-title">Importar Documento</div>
                <div class="module-text">Entrada única para notas, comprovantes, boletos, extratos e documentos financeiros.</div>
            </div>
        </div>
        <div class="arrow">›</div>
    </div>

    <div class="module-card">
        <div class="module-left">
            <div class="icon green">↻</div>
            <div>
                <div class="module-title">Conciliação Bancária</div>
                <div class="module-text">Cruzamento entre movimentos bancários, contas a pagar, contas a receber e comprovantes.</div>
            </div>
        </div>
        <div class="arrow">›</div>
    </div>

    <div class="module-card">
        <div class="module-left">
            <div class="icon purple">📁</div>
            <div>
                <div class="module-title">Processos Documentais</div>
                <div class="module-text">Controle de pendências, evidências e encerramento financeiro por documento.</div>
            </div>
        </div>
        <div class="arrow">›</div>
    </div>
</div>
""", unsafe_allow_html=True)


g1, g2 = st.columns(2)

with g1:
    st.markdown('<div class="panel"><div class="panel-title">Recebimentos x Pagamentos</div>', unsafe_allow_html=True)

    if not df.empty:
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
            height=320,
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        fig.update_traces(texttemplate="R$ %{text:,.2f}", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem movimentações para exibir.")

    st.markdown('</div>', unsafe_allow_html=True)


with g2:
    st.markdown('<div class="panel"><div class="panel-title">Status das movimentações</div>', unsafe_allow_html=True)

    if not df.empty:
        fig2 = px.pie(
            df,
            names="status",
            hole=0.62,
            color_discrete_sequence=["#2563eb", "#facc15", "#ef4444", "#22c55e"]
        )
        fig2.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=10, b=10),
            legend_title_text="",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Sem status para exibir.")

    st.markdown('</div>', unsafe_allow_html=True)


st.markdown('<div class="section-title">Movimentações financeiras</div>', unsafe_allow_html=True)

if not df.empty:
    df_show = df.copy()
    df_show["data"] = pd.to_datetime(df_show["data"], errors="coerce").dt.strftime("%d/%m/%Y")
    df_show["valor"] = df_show["valor"].apply(formatar_moeda)
    df_show = df_show[["data", "tipo", "descricao", "categoria", "valor", "status"]]
    df_show.columns = ["Data", "Tipo", "Descrição", "Categoria", "Valor", "Status"]
    st.dataframe(df_show, use_container_width=True, hide_index=True)
else:
    st.info("Nenhuma movimentação financeira cadastrada.")

st.caption("GOIA Finance Platform · Versão 0.8")
