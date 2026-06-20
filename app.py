import base64
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="GOIA Finance Platform",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def moeda(valor):
    return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def carregar_logo():
    for caminho in [Path("assets/logo_goia.png"), Path("imagens/LOGO GOIA.png")]:
        if caminho.exists():
            return base64.b64encode(caminho.read_bytes()).decode()
    return ""


df = pd.read_csv("dados/financeiro.csv")

recebimentos = df[df["tipo"] == "Receber"]["valor"].sum()
pagamentos = abs(df[df["tipo"] == "Pagar"]["valor"].sum())
saldo = recebimentos - pagamentos
pendencias = len(df[df["status"] == "Pendente"])
total = len(df)

logo_base64 = carregar_logo()

linhas = ""
for _, row in df.head(10).iterrows():
    valor = moeda(row["valor"])
    tipo = row["tipo"]
    status = row["status"]

    linhas += f"""
    <tr>
        <td>{row.get("data", "")}</td>
        <td>{tipo}</td>
        <td>{row.get("descricao", "")}</td>
        <td>{row.get("categoria", "")}</td>
        <td>{valor}</td>
        <td>{status}</td>
    </tr>
    """


st.markdown("""
<style>
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stHeader"],
[data-testid="stToolbar"] {
    display: none !important;
}

.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}
</style>
""", unsafe_allow_html=True)


html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
* {{
    box-sizing: border-box;
    font-family: Inter, Arial, sans-serif;
}}

body {{
    margin: 0;
    background: #f5f7ff;
    color: #0f172a;
}}

.app {{
    display: grid;
    grid-template-columns: 250px 1fr;
    min-height: 100vh;
}}

.sidebar {{
    background: linear-gradient(180deg, #071126 0%, #0b1733 60%, #050b18 100%);
    padding: 34px 22px;
    color: white;
}}

.logo {{
    width: 150px;
    margin-bottom: 42px;
}}

.menu-item {
    text-decoration: none;
    padding: 14px 16px;
    border-radius: 13px;
    margin-bottom: 10px;
    font-size: 14px;
    color: #e5e7eb;
}}

.menu-item.active {{
    background: #14285a;
    font-weight: 800;
}}

.sidebar-card {{
    margin-top: 76px;
    padding: 22px;
    border-radius: 20px;
    background: rgba(37,99,235,.12);
    border: 1px solid rgba(96,165,250,.25);
}}

.sidebar-card h3 {{
    font-size: 15px;
    margin: 14px 0 8px;
}}

.sidebar-card p {{
    font-size: 13px;
    color: #cbd5e1;
    line-height: 1.45;
}}

.main {{
    padding: 30px 42px 60px;
    background:
        radial-gradient(circle at top right, rgba(37,99,235,.10), transparent 28%),
        linear-gradient(135deg, #f8fafc 0%, #f1f5ff 48%, #ffffff 100%);
}}

.topbar {{
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 18px;
    color: #475569;
    font-size: 14px;
    margin-bottom: 24px;
}}

.avatar {{
    width: 42px;
    height: 42px;
    border-radius: 50%;
    background: #2563eb;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
}}

.hero {{
    display: grid;
    grid-template-columns: 1fr 300px;
    align-items: center;
    gap: 34px;
    padding: 46px 54px;
    border-radius: 28px;
    background: linear-gradient(135deg, rgba(255,255,255,.96), rgba(239,247,255,.92));
    border: 1px solid #e5e7eb;
    box-shadow: 0 22px 70px rgba(15,23,42,.08);
}}

.hero h1 {{
    margin: 0 0 14px;
    font-size: 36px;
    line-height: 1.1;
    letter-spacing: -.9px;
}}

.hero p {{
    max-width: 860px;
    margin: 0;
    color: #475569;
    font-size: 16px;
    line-height: 1.6;
}}

.wave {{
    height: 150px;
    border-radius: 20px;
    background: repeating-radial-gradient(ellipse at center, rgba(14,165,233,.35) 0 1px, transparent 2px 18px);
    opacity: .45;
}}

.kpis {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-top: 20px;
}}

.card {{
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 24px;
    padding: 26px;
    box-shadow: 0 18px 48px rgba(15,23,42,.07);
}}

.kpi-label {{
    color: #475569;
    font-size: 14px;
    font-weight: 800;
}}

.kpi-value {{
    color: #020617;
    font-size: 30px;
    font-weight: 950;
    margin-top: 8px;
}}

.kpi-sub {{
    color: #64748b;
    font-size: 13px;
    margin-top: 6px;
}}

.trend {{
    margin-top: 14px;
    font-size: 13px;
    font-weight: 800;
}}

.green {{ color: #16a34a; }}
.red {{ color: #dc2626; }}
.purple {{ color: #7c3aed; }}

.section-title {{
    font-size: 22px;
    font-weight: 950;
    margin: 28px 0 14px;
}}

.modules {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
}}

.module-title {{
    font-weight: 950;
    font-size: 16px;
    margin-bottom: 8px;
}}

.module-text {{
    color: #64748b;
    font-size: 14px;
    line-height: 1.5;
}}

.charts {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-top: 16px;
}}

.chart {{
    min-height: 280px;
}}

.bar-area {{
    height: 220px;
    display: flex;
    align-items: end;
    justify-content: center;
    gap: 90px;
    border-bottom: 1px solid #cbd5e1;
}}

.bar {{
    width: 150px;
    border-radius: 8px 8px 0 0;
    position: relative;
    text-align: center;
}}

.bar span {{
    position: absolute;
    top: -28px;
    left: 0;
    right: 0;
    color: #64748b;
    font-size: 13px;
}}

.bar.greenbar {{
    height: 175px;
    background: #22c55e;
}}

.bar.redbar {{
    height: 120px;
    background: #ef4444;
}}

.donut-wrap {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 70px;
    height: 220px;
}}

.donut {{
    width: 170px;
    height: 170px;
    border-radius: 50%;
    background: conic-gradient(#4f46e5 0 72%, #facc15 72% 91%, #ef4444 91% 100%);
    position: relative;
}}

.donut::after {{
    content: "Total\\A {total}\\A movimentações";
    white-space: pre;
    position: absolute;
    width: 104px;
    height: 104px;
    background: white;
    border-radius: 50%;
    top: 33px;
    left: 33px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: #64748b;
    font-size: 13px;
    line-height: 1.4;
}}

.legend div {{
    margin-bottom: 16px;
    font-size: 14px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 18px;
    overflow: hidden;
    border: 1px solid #e5e7eb;
}}

th, td {{
    text-align: left;
    padding: 13px 16px;
    font-size: 14px;
    border-bottom: 1px solid #e5e7eb;
}}

th {{
    background: #f8fafc;
    color: #475569;
}}

.footer {{
    margin-top: 24px;
    color: #94a3b8;
    font-size: 13px;
}}
</style>
</head>

<body>
<div class="app">

<aside class="sidebar">
    <img class="logo" src="data:image/png;base64,{logo_base64}">

    <a class="menu-item active" href="/">Dashboard</a>
    <a class="menu-item" href="/Importar_Documento">Importar Documento</a>
    <a class="menu-item" href="/Clientes">Clientes</a>
    <a class="menu-item" href="/Fornecedores">Fornecedores</a>
    <a class="menu-item" href="/Contas_a_Receber">Contas a Receber</a>
    <a class="menu-item" href="/Contas_a_Pagar">Contas a Pagar</a>
    <a class="menu-item" href="/Compras">Compras</a>
    <a class="menu-item" href="/Produtos_Estoque">Produtos Estoque</a>
    <a class="menu-item" href="/Vendas">Vendas</a>
    <a class="menu-item" href="/Processos_Documentais">Processos Documentais</a>
    <a class="menu-item" href="/Conciliacao_Bancaria">Conciliação Bancária</a>
    <a class="menu-item" href="/Relatorios">Relatórios</a>

    <div class="sidebar-card">
        <div style="font-size:28px;">✦</div>
        <h3>GOIA Finance Platform</h3>
        <p>Automação financeira document-driven para empresas que precisam de controle, evidência e conciliação.</p>
    </div>
</aside>

<main class="main">

    <div class="topbar">
        <span>18 de junho de 2026</span>
        <span>🔔</span>
        <div class="avatar">GS</div>
        <div><b>Glauber</b><br><span style="font-size:12px;color:#64748b;">Administrador</span></div>
    </div>

    <section class="hero">
        <div>
            <h1>Inteligência que transforma finanças</h1>
            <p>Automação financeira document-driven para importar documentos, estruturar compras e vendas, controlar contas a pagar e receber, acompanhar processos documentais e apoiar a conciliação bancária.</p>
        </div>
        <div class="wave"></div>
    </section>

    <section class="kpis">
        <div class="card">
            <div class="kpi-label">Recebimentos</div>
            <div class="kpi-value">{moeda(recebimentos)}</div>
            <div class="kpi-sub">Total de receitas</div>
            <div class="trend green">↑ 12,5% vs. mês anterior</div>
        </div>

        <div class="card">
            <div class="kpi-label">Pagamentos</div>
            <div class="kpi-value">{moeda(pagamentos)}</div>
            <div class="kpi-sub">Total de despesas</div>
            <div class="trend red">↑ 8,3% vs. mês anterior</div>
        </div>

        <div class="card">
            <div class="kpi-label">Saldo operacional</div>
            <div class="kpi-value">{moeda(saldo)}</div>
            <div class="kpi-sub">Resultado do período</div>
            <div class="trend green">↑ 18,7% vs. mês anterior</div>
        </div>

        <div class="card">
            <div class="kpi-label">Pendências</div>
            <div class="kpi-value">{pendencias}</div>
            <div class="kpi-sub">Itens pendentes</div>
            <div class="trend purple">Ver detalhes →</div>
        </div>
    </section>

    <div class="section-title">Módulos principais</div>

    <section class="modules">
        <div class="card">
            <div class="module-title">Importar Documento</div>
            <div class="module-text">Entrada única para notas, comprovantes, boletos, extratos e documentos financeiros.</div>
        </div>
        <div class="card">
            <div class="module-title">Conciliação Bancária</div>
            <div class="module-text">Cruzamento entre movimentos bancários, contas a pagar, contas a receber e comprovantes.</div>
        </div>
        <div class="card">
            <div class="module-title">Processos Documentais</div>
            <div class="module-text">Controle de pendências, evidências e encerramento financeiro por documento.</div>
        </div>
    </section>

    <section class="charts">
        <div class="card chart">
            <div class="section-title" style="margin-top:0;">Recebimentos x Pagamentos</div>
            <div class="bar-area">
                <div class="bar greenbar"><span>{moeda(recebimentos)}</span></div>
                <div class="bar redbar"><span>{moeda(pagamentos)}</span></div>
            </div>
        </div>

        <div class="card chart">
            <div class="section-title" style="margin-top:0;">Status das movimentações</div>
            <div class="donut-wrap">
                <div class="donut"></div>
                <div class="legend">
                    <div>● Baixada</div>
                    <div>● Pendente</div>
                    <div>● Cancelado</div>
                </div>
            </div>
        </div>
    </section>

    <div class="section-title">Movimentações financeiras</div>

    <table>
        <thead>
            <tr>
                <th>Data</th>
                <th>Tipo</th>
                <th>Descrição</th>
                <th>Categoria</th>
                <th>Valor</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {linhas}
        </tbody>
    </table>

    <div class="footer">GOIA Finance Platform · Versão 1.2</div>

</main>
</div>
</body>
</html>
"""

components.html(html, height=1200, scrolling=True)
