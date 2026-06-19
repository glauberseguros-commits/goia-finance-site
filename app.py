import base64
from pathlib import Path

import pandas as pd
import sqlite3
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
    for caminho in [
        Path("assets/logo_goia.png"),
        Path("imagens/LOGO GOIA.png")
    ]:
        if caminho.exists():
            return base64.b64encode(caminho.read_bytes()).decode()
    return ""



def buscar_ultimo_documento():
    try:
        conn = sqlite3.connect("bd/gofinance.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                tipo_documento,
                direcao,
                nome_emitente,
                nome_destinatario,
                valor,
                status_processamento,
                numero_nfe,
                serie_nfe,
                data_emissao
            FROM documentos
            WHERE empresa_id = 1
            ORDER BY id DESC
            LIMIT 1
        """)

        doc = cur.fetchone()

        if not doc:
            conn.close()
            return None

        cur.execute("""
            SELECT COUNT(*) AS total
            FROM processo_pendencias
            WHERE empresa_id = 1
              AND processo_id IN (
                  SELECT processo_id
                  FROM processo_documentos
                  WHERE documento_id = ?
                    AND empresa_id = 1
              )
        """, (doc["id"],))

        pendencias_doc = cur.fetchone()["total"]

        conn.close()

        return dict(doc) | {"pendencias_doc": pendencias_doc}

    except Exception:
        return None


df = pd.read_csv("dados/financeiro.csv")

recebimentos = df[df["tipo"] == "Receber"]["valor"].sum()
pagamentos = abs(df[df["tipo"] == "Pagar"]["valor"].sum())
saldo = recebimentos - pagamentos
pendencias = len(df[df["status"] == "Pendente"])
total = len(df)

logo_base64 = carregar_logo()

linhas = ""
for _, row in df.head(10).iterrows():
    tipo = row.get("tipo", "")
    status = row.get("status", "")
    valor = moeda(row.get("valor", 0))

    classe_tipo = "tipo-receber" if tipo == "Receber" else "tipo-pagar"

    status_normalizado = str(status).lower()
    if "receb" in status_normalizado or "baix" in status_normalizado:
        classe_status = "status-ok"
    elif "pend" in status_normalizado:
        classe_status = "status-pendente"
    elif "pago" in status_normalizado:
        classe_status = "status-pago"
    else:
        classe_status = "status-neutro"

    linhas += f"""
    <tr>
        <td>{row.get("data", "")}</td>
        <td><span class="badge {classe_tipo}">{tipo}</span></td>
        <td>{row.get("descricao", "")}</td>
        <td>{row.get("categoria", "")}</td>
        <td class="valor">{valor}</td>
        <td><span class="badge {classe_status}">{status}</span></td>
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

iframe {
    display: block;
}
</style>
""", unsafe_allow_html=True)



ultimo_documento = buscar_ultimo_documento()

if ultimo_documento:
    numero = ultimo_documento.get("numero_nfe") or ultimo_documento.get("id")
    serie = ultimo_documento.get("serie_nfe") or ""
    direcao_doc = ultimo_documento.get("direcao") or "Documento financeiro"
    tipo_doc = ultimo_documento.get("tipo_documento") or "Documento"
    valor_doc = moeda(ultimo_documento.get("valor") or 0)
    status_doc = ultimo_documento.get("status_processamento") or "Processado"
    pend_doc = ultimo_documento.get("pendencias_doc") or 0

    if "Venda" in direcao_doc:
        parte_doc = ultimo_documento.get("nome_destinatario") or "Cliente identificado"
        acao_doc = "Conta a receber criada"
    elif "Compra" in direcao_doc or "Despesa" in direcao_doc:
        parte_doc = ultimo_documento.get("nome_emitente") or "Fornecedor identificado"
        acao_doc = "Conta a pagar criada"
    else:
        parte_doc = ultimo_documento.get("nome_emitente") or ultimo_documento.get("nome_destinatario") or "Contraparte identificada"
        acao_doc = "Documento salvo para análise"

    titulo_doc = f"{tipo_doc} {numero}"
    if serie:
        titulo_doc += f" · Série {serie}"

    doc_html = f"""
    <section class="doc-intel">
        <div>
            <div class="eyebrow">Inteligência documental</div>
            <h2>{titulo_doc}</h2>
            <p>{parte_doc}</p>
        </div>

        <div class="doc-kpis">
            <div>
                <span>Valor identificado</span>
                <strong>{valor_doc}</strong>
            </div>
            <div>
                <span>Classificação</span>
                <strong>{direcao_doc}</strong>
            </div>
            <div>
                <span>Status</span>
                <strong>{status_doc}</strong>
            </div>
            <div>
                <span>Pendências</span>
                <strong>{pend_doc}</strong>
            </div>
        </div>

        <div class="doc-flow">
            <div>PDF recebido</div>
            <div>Texto extraído</div>
            <div>Documento classificado</div>
            <div>{acao_doc}</div>
            <div>Processo documental criado</div>
        </div>
    </section>
    """
else:
    doc_html = """
    <section class="doc-intel">
        <div>
            <div class="eyebrow">Inteligência documental</div>
            <h2>Nenhum documento processado ainda</h2>
            <p>Importe uma NF-e, boleto, comprovante ou extrato para iniciar o fluxo document-driven.</p>
        </div>
    </section>
    """


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
    grid-template-columns: 210px 1fr;
    min-height: 100vh;
}}

.sidebar {{
    background: linear-gradient(180deg, #071126 0%, #0b1733 60%, #050b18 100%);
    padding: 28px 18px;
    color: white;
}}

.logo-box {{
    padding: 0 0 34px;
}}

.logo {{
    width: 138px;
    display: block;
}}

.menu-item {{
    padding: 13px 14px;
    border-radius: 13px;
    margin-bottom: 8px;
    font-size: 14px;
    color: #e5e7eb;
}}

.menu-item.active {{
    background: #14285a;
    font-weight: 800;
}}

.main {{
    padding: 26px 38px 52px;
    background:
        radial-gradient(circle at top right, rgba(37,99,235,.12), transparent 28%),
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
    padding: 36px 46px;
    border-radius: 28px;
    background: linear-gradient(135deg, rgba(255,255,255,.97), rgba(239,247,255,.92));
    border: 1px solid #e5e7eb;
    box-shadow: 0 22px 70px rgba(15,23,42,.08);
}}

.hero h1 {{
    margin: 0 0 14px;
    font-size: 38px;
    line-height: 1.08;
    letter-spacing: -.9px;
}}

.hero p {{
    max-width: 900px;
    margin: 0;
    color: #475569;
    font-size: 16.5px;
    line-height: 1.65;
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

.kpi-card {{
    display: grid;
    grid-template-columns: 54px 1fr;
    gap: 16px;
    align-items: start;
    min-height: 152px;
}}

.icon {{
    width: 52px;
    height: 52px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    font-weight: 900;
}}

.icon.green {{
    background: #dcfce7;
    color: #16a34a;
}}

.icon.red {{
    background: #fee2e2;
    color: #dc2626;
}}

.icon.blue {{
    background: #dbeafe;
    color: #2563eb;
}}

.icon.purple {{
    background: #ede9fe;
    color: #7c3aed;
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

.green-text {{ color: #16a34a; }}
.red-text {{ color: #dc2626; }}
.purple-text {{ color: #7c3aed; }}

.section-title {{
    font-size: 23px;
    font-weight: 950;
    margin: 26px 0 14px;
}}

.modules {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
}}

.module-card {{
    display: grid;
    grid-template-columns: 54px 1fr 20px;
    gap: 16px;
    align-items: center;
    min-height: 108px;
}}

.module-title {{
    font-weight: 950;
    font-size: 16px;
    margin-bottom: 8px;
}}

.module-text {{
    color: #64748b;
    font-size: 13.5px;
    line-height: 1.5;
}}

.arrow {{
    color: #64748b;
    font-size: 24px;
}}


.doc-intel {{
    margin-top: 18px;
    padding: 26px;
    border-radius: 24px;
    background: linear-gradient(135deg, #ffffff, #f8fbff);
    border: 1px solid #e5e7eb;
    box-shadow: 0 18px 48px rgba(15,23,42,.07);
}}

.doc-intel .eyebrow {{
    color: #2563eb;
    font-size: 13px;
    font-weight: 950;
    text-transform: uppercase;
    letter-spacing: .08em;
    margin-bottom: 8px;
}}

.doc-intel h2 {{
    margin: 0;
    font-size: 24px;
    letter-spacing: -.4px;
}}

.doc-intel p {{
    margin: 8px 0 0;
    color: #64748b;
    font-size: 14px;
}}

.doc-kpis {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-top: 22px;
}}

.doc-kpis div {{
    padding: 16px;
    border-radius: 18px;
    background: #f8fafc;
    border: 1px solid #e5e7eb;
}}

.doc-kpis span {{
    display: block;
    color: #64748b;
    font-size: 12px;
    font-weight: 800;
    margin-bottom: 8px;
}}

.doc-kpis strong {{
    color: #0f172a;
    font-size: 16px;
}}

.doc-flow {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
    margin-top: 18px;
}}

.doc-flow div {{
    padding: 12px 10px;
    border-radius: 999px;
    background: #eef2ff;
    color: #3730a3;
    text-align: center;
    font-size: 12px;
    font-weight: 900;
}}

.charts {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-top: 16px;
}}

.chart {{
    min-height: 300px;
}}

.chart-title {{
    font-size: 20px;
    font-weight: 950;
    margin-bottom: 20px;
}}

.bar-area {{
    height: 225px;
    display: flex;
    align-items: end;
    justify-content: center;
    gap: 92px;
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
    height: 225px;
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

.dot {{
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 10px;
}}

.dot.blue {{ background: #4f46e5; }}
.dot.yellow {{ background: #facc15; }}
.dot.red {{ background: #ef4444; }}

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
    font-weight: 800;
}}

.valor {{
    font-weight: 800;
}}

.badge {{
    display: inline-block;
    padding: 5px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 800;
}}

.tipo-receber {{
    background: #dcfce7;
    color: #15803d;
}}

.tipo-pagar {{
    background: #e2e8f0;
    color: #334155;
}}

.status-ok {{
    background: #dcfce7;
    color: #15803d;
}}

.status-pendente {{
    background: #fef3c7;
    color: #b45309;
}}

.status-pago {{
    background: #dbeafe;
    color: #1d4ed8;
}}

.status-neutro {{
    background: #f1f5f9;
    color: #334155;
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
    <div class="logo-box">
        <img class="logo" src="data:image/png;base64,{logo_base64}">
    </div>

    <div class="menu-item active">Dashboard</div>
    <div class="menu-item">Importar Documento</div>
    <div class="menu-item">Contas a Receber</div>
    <div class="menu-item">Contas a Pagar</div>
    <div class="menu-item">Compras</div>
    <div class="menu-item">Produtos Estoque</div>
    <div class="menu-item">Vendas</div>
    <div class="menu-item">Processos Documentais</div>
    <div class="menu-item">Conciliação Bancária</div>
    <div class="menu-item">Relatórios</div>

    <div class="sidebar-card">
        
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
        <div class="card kpi-card">
            <div class="icon green">↗</div>
            <div>
                <div class="kpi-label">Recebimentos</div>
                <div class="kpi-value">{moeda(recebimentos)}</div>
                <div class="kpi-sub">Total de receitas</div>
                <div class="trend green-text">↑ 12,5% vs. mês anterior</div>
            </div>
        </div>

        <div class="card kpi-card">
            <div class="icon red">↘</div>
            <div>
                <div class="kpi-label">Pagamentos</div>
                <div class="kpi-value">{moeda(pagamentos)}</div>
                <div class="kpi-sub">Total de despesas</div>
                <div class="trend red-text">↑ 8,3% vs. mês anterior</div>
            </div>
        </div>

        <div class="card kpi-card">
            <div class="icon blue">▦</div>
            <div>
                <div class="kpi-label">Saldo operacional</div>
                <div class="kpi-value">{moeda(saldo)}</div>
                <div class="kpi-sub">Resultado do período</div>
                <div class="trend green-text">↑ 18,7% vs. mês anterior</div>
            </div>
        </div>

        <div class="card kpi-card">
            <div class="icon purple">▣</div>
            <div>
                <div class="kpi-label">Pendências</div>
                <div class="kpi-value">{pendencias}</div>
                <div class="kpi-sub">Itens pendentes</div>
                <div class="trend purple-text">Ver detalhes →</div>
            </div>
        </div>
    </section>

    <div class="section-title">Módulos principais</div>

    <section class="modules">
        <div class="card module-card">
            <div class="icon blue">▤</div>
            <div>
                <div class="module-title">Importar Documento</div>
                <div class="module-text">Entrada única para notas, comprovantes, boletos, extratos e documentos financeiros.</div>
            </div>
            <div class="arrow">›</div>
        </div>

        <div class="card module-card">
            <div class="icon green">↻</div>
            <div>
                <div class="module-title">Conciliação Bancária</div>
                <div class="module-text">Cruzamento entre movimentos bancários, contas a pagar, contas a receber e comprovantes.</div>
            </div>
            <div class="arrow">›</div>
        </div>

        <div class="card module-card">
            <div class="icon purple">▭</div>
            <div>
                <div class="module-title">Processos Documentais</div>
                <div class="module-text">Controle de pendências, evidências e encerramento financeiro por documento.</div>
            </div>
            <div class="arrow">›</div>
        </div>
    </section>

    {doc_html}

    <section class="charts">
        <div class="card chart">
            <div class="chart-title">Recebimentos x Pagamentos</div>
            <div class="bar-area">
                <div class="bar greenbar"><span>{moeda(recebimentos)}</span></div>
                <div class="bar redbar"><span>{moeda(pagamentos)}</span></div>
            </div>
        </div>

        <div class="card chart">
            <div class="chart-title">Status das movimentações</div>
            <div class="donut-wrap">
                <div class="donut"></div>
                <div class="legend">
                    <div><span class="dot blue"></span>Baixada</div>
                    <div><span class="dot yellow"></span>Pendente</div>
                    <div><span class="dot red"></span>Cancelado</div>
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

    <div class="footer">GOIA Finance Platform · Versão 1.3 · Dia 2</div>

</main>
</div>
</body>
</html>
"""

components.html(html, height=1250, scrolling=True)



