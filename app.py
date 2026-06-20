import base64
from pathlib import Path
import pandas as pd
import streamlit as st
import sqlite3
import hashlib
import streamlit.components.v1 as components

st.set_page_config(
    page_title="GOIA Finance Platform",
    page_icon="💰",
    layout="wide"
)

# =========================
# LOGIN / MULTIEMPRESA
# =========================

AUTH_DB_PATH = "bd/gofinance.db"

def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def buscar_usuario(email, senha):
    conn = sqlite3.connect(AUTH_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nome, email
        FROM usuarios
        WHERE email = ?
          AND senha_hash = ?
          AND ativo = 1
    """, (email.strip().lower(), hash_senha(senha)))

    usuario = cur.fetchone()

    if not usuario:
        conn.close()
        return None, []

    cur.execute("""
        SELECT e.id, e.nome, e.cnpj_cpf, ue.perfil_empresa
        FROM usuario_empresas ue
        JOIN empresas e ON e.id = ue.empresa_id
        WHERE ue.usuario_id = ?
          AND ue.ativo = 1
          AND COALESCE(e.status_assinatura, 'Ativa') = 'Ativa'
        ORDER BY e.nome
    """, (usuario["id"],))

    empresas = cur.fetchall()
    conn.close()

    return dict(usuario), [dict(e) for e in empresas]

def exigir_login():
    if st.session_state.get("logado") and st.session_state.get("empresa_id"):
        return

    st.markdown("## GOIA Finance Platform")
    st.subheader("Acesso ao sistema")
    st.caption("Entre com seu usuário para acessar as empresas vinculadas à sua assinatura.")

    with st.form("form_login"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        usuario, empresas = buscar_usuario(email, senha)

        if not usuario:
            st.error("Usuário ou senha inválidos.")
            st.stop()

        if not empresas:
            st.error("Usuário sem empresa vinculada.")
            st.stop()

        st.session_state["logado"] = True
        st.session_state["usuario_id"] = usuario["id"]
        st.session_state["usuario_nome"] = usuario["nome"]

        if len(empresas) == 1:
            st.session_state["empresa_id"] = empresas[0]["id"]
            st.session_state["empresa_nome"] = empresas[0]["nome"]
            st.rerun()

        st.session_state["empresas_usuario"] = empresas
        st.rerun()

    if st.session_state.get("logado") and not st.session_state.get("empresa_id"):
        empresas = st.session_state.get("empresas_usuario", [])
        nomes = [e["nome"] for e in empresas]
        escolhida = st.selectbox("Selecione a empresa", nomes)

        if st.button("Acessar empresa"):
            empresa = next(e for e in empresas if e["nome"] == escolhida)
            st.session_state["empresa_id"] = empresa["id"]
            st.session_state["empresa_nome"] = empresa["nome"]
            st.rerun()

    st.stop()

exigir_login()



df = pd.read_csv("dados/financeiro.csv")

recebimentos = df[df["tipo"] == "Receber"]["valor"].sum()
pagamentos = abs(df[df["tipo"] == "Pagar"]["valor"].sum())
saldo = recebimentos - pagamentos
pendencias = len(df[df["status"] == "Pendente"])


def moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


logo_path = Path("assets/logo_goia.png")
if not logo_path.exists():
    logo_path = Path("imagens/LOGO GOIA.png")

logo_base64 = base64.b64encode(logo_path.read_bytes()).decode()

linhas_tabela = ""
for _, row in df.head(8).iterrows():
    tipo = row.get("tipo", "")
    status = row.get("status", "")
    valor = row.get("valor", 0)

    badge_tipo = "green" if tipo == "Receber" else "gray"
    badge_status = "green" if status == "Baixada" else "yellow"

    linhas_tabela += f"""
    <tr>
        <td>{row.get("data", "")}</td>
        <td><span class="badge {badge_tipo}">{tipo}</span></td>
        <td>{row.get("descricao", "")}</td>
        <td>{row.get("categoria", "")}</td>
        <td>{moeda(valor)}</td>
        <td><span class="badge {badge_status}">{status}</span></td>
    </tr>
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
    background: #f6f8ff;
    color: #0f172a;
}}

.app {{
    display: grid;
    grid-template-columns: 250px 1fr;
    min-height: 1180px;
}}

.sidebar {{
    background: linear-gradient(180deg, #071126 0%, #0b1733 60%, #050b18 100%);
    padding: 34px 22px;
    color: white;
}}

.sidebar img {{
    width: 150px;
    margin-bottom: 38px;
}}

.menu-item {{
    padding: 13px 14px;
    border-radius: 12px;
    margin-bottom: 8px;
    font-size: 14px;
    color: #e5e7eb;
}}

.menu-item.active {{
    background: #14285a;
    font-weight: 800;
}}

.sidebar-card {{
    margin-top: 80px;
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
    grid-template-columns: 260px 1fr 260px;
    align-items: center;
    gap: 34px;
    padding: 34px 42px;
    border-radius: 26px;
    background: linear-gradient(135deg, rgba(255,255,255,.96), rgba(239,247,255,.92));
    border: 1px solid #e5e7eb;
    box-shadow: 0 22px 70px rgba(15,23,42,.08);
}}

.hero img {{
    width: 245px;
}}

.hero h1 {{
    margin: 0 0 10px;
    font-size: 30px;
    letter-spacing: -.8px;
}}

.hero p {{
    color: #475569;
    font-size: 15px;
    line-height: 1.55;
    margin: 0;
}}

.wave {{
    height: 120px;
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
    padding: 24px;
    box-shadow: 0 18px 48px rgba(15,23,42,.07);
}}

.kpi {{
    display: flex;
    gap: 18px;
}}

.icon {{
    width: 52px;
    height: 52px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
}}

.icon.green {{ background: #dcfce7; color: #16a34a; }}
.icon.red {{ background: #fee2e2; color: #dc2626; }}
.icon.blue {{ background: #dbeafe; color: #2563eb; }}
.icon.purple {{ background: #ede9fe; color: #7c3aed; }}

.label {{
    color: #475569;
    font-size: 14px;
    font-weight: 800;
}}

.value {{
    font-size: 28px;
    font-weight: 950;
    margin-top: 6px;
}}

.sub {{
    color: #64748b;
    font-size: 13px;
    margin-top: 4px;
}}

.trend {{
    margin-top: 12px;
    font-size: 13px;
    font-weight: 800;
}}

.positive {{ color: #16a34a; }}
.negative {{ color: #dc2626; }}
.purple-text {{ color: #7c3aed; }}

.section {{
    font-size: 22px;
    font-weight: 950;
    margin: 26px 0 12px;
}}

.modules {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
}}

.module {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    min-height: 110px;
}}

.module-left {{
    display: flex;
    align-items: center;
    gap: 18px;
}}

.module-title {{
    font-weight: 900;
    margin-bottom: 6px;
}}

.module-text {{
    color: #64748b;
    font-size: 13px;
    line-height: 1.45;
}}

.charts {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-top: 16px;
}}

.chart-title {{
    font-size: 18px;
    font-weight: 900;
    margin-bottom: 22px;
}}

.bar-area {{
    height: 260px;
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
    color: #64748b;
    font-size: 13px;
}}

.bar span {{
    position: absolute;
    top: -24px;
    left: 0;
    right: 0;
}}

.bar.green {{ height: 180px; background: #22c55e; }}
.bar.red {{ height: 125px; background: #ef4444; }}

.donut-wrap {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 60px;
    height: 260px;
}}

.donut {{
    width: 180px;
    height: 180px;
    border-radius: 50%;
    background: conic-gradient(#2563eb 0 80%, #facc15 80% 95%, #ef4444 95% 100%);
    position: relative;
}}

.donut::after {{
    content: "Total\\A {len(df)}\\A movimentações";
    white-space: pre;
    position: absolute;
    width: 108px;
    height: 108px;
    background: white;
    border-radius: 50%;
    top: 36px;
    left: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: #64748b;
    font-size: 13px;
    line-height: 1.4;
}}

.legend div {{
    margin-bottom: 18px;
    font-size: 14px;
}}

.dot {{
    display: inline-block;
    width: 11px;
    height: 11px;
    border-radius: 50%;
    margin-right: 10px;
}}

.dot.blue {{ background: #2563eb; }}
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
}}

.badge {{
    padding: 5px 9px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 800;
}}

.badge.green {{ background: #dcfce7; color: #15803d; }}
.badge.gray {{ background: #f1f5f9; color: #334155; }}
.badge.yellow {{ background: #fef3c7; color: #b45309; }}

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
        <img src="data:image/png;base64,{logo_base64}">

        <div class="menu-item active">⌂ Dashboard</div>
        <div class="menu-item">⇪ Importar Documento</div>
        <div class="menu-item">▣ Contas a Receber</div>
        <div class="menu-item">▣ Contas a Pagar</div>
        <div class="menu-item">🛒 Compras</div>
        <div class="menu-item">▤ Produtos Estoque</div>
        <div class="menu-item">▧ Vendas</div>
        <div class="menu-item">▣ Processos Documentais</div>
        <div class="menu-item">▥ Conciliação Bancária</div>
        <div class="menu-item">▥ Relatórios</div>

        <div class="sidebar-card">
            <div style="font-size:28px;">✦</div>
            <h3>GOIA Finance Platform</h3>
            <p>Automação financeira document-driven para empresas que precisam de controle, evidência e conciliação.</p>
        </div>
    </aside>

    <main class="main">
        <div class="topbar">
            <span>📅 18 de junho de 2026</span>
            <span>🔔</span>
            <div class="avatar">GS</div>
            <div><b>Glauber</b><br><span style="font-size:12px;color:#64748b;">Administrador</span></div>
        </div>

        <section class="hero">
            <img src="data:image/png;base64,{logo_base64}">
            <div>
                <h1>Inteligência que transforma finanças</h1>
                <p>Automação financeira document-driven para importar documentos, estruturar compras e vendas, controlar contas a pagar e receber, acompanhar processos documentais e apoiar a conciliação bancária.</p>
            </div>
            <div class="wave"></div>
        </section>

        <section class="kpis">
            <div class="card kpi">
                <div class="icon green">↗</div>
                <div>
                    <div class="label">Recebimentos</div>
                    <div class="value">{moeda(recebimentos)}</div>
                    <div class="sub">Total de receitas</div>
                    <div class="trend positive">↑ 12,5% vs. mês anterior</div>
                </div>
            </div>

            <div class="card kpi">
                <div class="icon red">↘</div>
                <div>
                    <div class="label">Pagamentos</div>
                    <div class="value">{moeda(pagamentos)}</div>
                    <div class="sub">Total de despesas</div>
                    <div class="trend negative">↑ 8,3% vs. mês anterior</div>
                </div>
            </div>

            <div class="card kpi">
                <div class="icon blue">🏦</div>
                <div>
                    <div class="label">Saldo operacional</div>
                    <div class="value">{moeda(saldo)}</div>
                    <div class="sub">Resultado do período</div>
                    <div class="trend positive">↑ 18,7% vs. mês anterior</div>
                </div>
            </div>

            <div class="card kpi">
                <div class="icon purple">▣</div>
                <div>
                    <div class="label">Pendências</div>
                    <div class="value">{pendencias}</div>
                    <div class="sub">Itens pendentes</div>
                    <div class="trend purple-text">Ver detalhes →</div>
                </div>
            </div>
        </section>

        <div class="section">Módulos principais</div>

        <section class="modules">
            <div class="card module">
                <div class="module-left">
                    <div class="icon blue">📄</div>
                    <div>
                        <div class="module-title">Importar Documento</div>
                        <div class="module-text">Entrada única para notas, comprovantes, boletos, extratos e documentos financeiros.</div>
                    </div>
                </div>
                <div>›</div>
            </div>

            <div class="card module">
                <div class="module-left">
                    <div class="icon green">↻</div>
                    <div>
                        <div class="module-title">Conciliação Bancária</div>
                        <div class="module-text">Cruzamento entre movimentos bancários, contas a pagar, contas a receber e comprovantes.</div>
                    </div>
                </div>
                <div>›</div>
            </div>

            <div class="card module">
                <div class="module-left">
                    <div class="icon purple">📁</div>
                    <div>
                        <div class="module-title">Processos Documentais</div>
                        <div class="module-text">Controle de pendências, evidências e encerramento financeiro por documento.</div>
                    </div>
                </div>
                <div>›</div>
            </div>
        </section>

        <section class="charts">
            <div class="card">
                <div class="chart-title">Recebimentos x Pagamentos</div>
                <div class="bar-area">
                    <div class="bar green"><span>{moeda(recebimentos)}</span></div>
                    <div class="bar red"><span>{moeda(pagamentos)}</span></div>
                </div>
            </div>

            <div class="card">
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

        <div class="section">Movimentações financeiras</div>

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
                {linhas_tabela}
            </tbody>
        </table>

        <div class="footer">GOIA Finance Platform · Versão 0.9</div>
    </main>

</div>
</body>
</html>
"""

components.html(html, height=1180, scrolling=True)
