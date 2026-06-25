import os
import hashlib
import sqlite3
import pandas as pd
import streamlit as st

from utils.db import conectar_banco

st.set_page_config(
    page_title="Admin GOIA",
    page_icon="🛡️",
    layout="wide"
)


def aplicar_estilo_admin():
    st.markdown("""
    <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(49,46,129,.16), transparent 34%),
                linear-gradient(135deg, #f8fafc 0%, #eef2ff 50%, #f8fafc 100%) !important;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #111827 100%) !important;
        }

        [data-testid="stSidebar"] * {
            color: #f8fafc !important;
            opacity: 1 !important;
            font-weight: 700 !important;
        }

        .block-container {
            max-width: 1220px !important;
            padding-top: 3rem !important;
        }

        .admin-login-card {
            max-width: 720px;
            margin: 8vh auto 30px auto;
            padding: 44px 48px;
            border-radius: 30px;
            background: rgba(255,255,255,.96);
            border: 1px solid rgba(148,163,184,.35);
            box-shadow: 0 30px 90px rgba(15,23,42,.18);
        }

        .admin-badge {
            display: inline-flex;
            padding: 8px 14px;
            border-radius: 999px;
            background: #eef2ff;
            color: #312e81;
            font-size: 12px;
            font-weight: 900;
            letter-spacing: .12em;
            text-transform: uppercase;
            margin-bottom: 18px;
        }

        .admin-title {
            color: #0f172a;
            font-size: 46px;
            font-weight: 950;
            letter-spacing: -.045em;
            line-height: 1.05;
            margin-bottom: 12px;
        }

        .admin-subtitle {
            color: #334155;
            font-size: 16px;
            font-weight: 600;
        }

        .admin-hero {
            padding: 42px 44px;
            border-radius: 28px;
            background: linear-gradient(135deg, #0f172a 0%, #312e81 100%);
            box-shadow: 0 28px 70px rgba(30,41,59,.24);
            margin-bottom: 28px;
        }

        .admin-hero small {
            color: #5eead4;
            letter-spacing: .17em;
            font-weight: 900;
            text-transform: uppercase;
        }

        .admin-hero h1 {
            color: white;
            font-size: 44px;
            font-weight: 950;
            letter-spacing: -.045em;
            margin: 12px 0;
        }

        .admin-hero p {
            color: #dbeafe;
            font-size: 16px;
            font-weight: 500;
            margin: 0;
        }

        div.stButton > button {
            background: linear-gradient(135deg, #ff5a3c 0%, #ef4444 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 14px !important;
            font-weight: 900 !important;
            box-shadow: 0 16px 34px rgba(239,68,68,.30);
        }

        [data-testid="stTextInput"] input,
        [data-testid="stSelectbox"] div,
        textarea {
            border-radius: 14px !important;
            border: 1px solid #94a3b8 !important;
            background: white !important;
            color: #0f172a !important;
            font-weight: 600 !important;
        }

        div[data-testid="metric-container"] {
            background: rgba(255,255,255,.96) !important;
            border: 1px solid rgba(148,163,184,.35) !important;
            border-radius: 22px !important;
            padding: 24px !important;
            box-shadow: 0 18px 42px rgba(15,23,42,.10) !important;
        }

        div[data-testid="metric-container"] label,
        div[data-testid="metric-container"] p {
            color: #1e293b !important;
            font-weight: 850 !important;
        }

        div[data-testid="metric-container"] [data-testid="stMetricValue"] {
            color: #0f172a !important;
            font-size: 42px !important;
            font-weight: 950 !important;
        }

        [data-testid="stAlert"] {
            border-radius: 16px !important;
            border: 1px solid rgba(99,102,241,.28) !important;
        }
    </style>
    """, unsafe_allow_html=True)


def conectar():
    return conectar_banco()


def hash_senha(senha):
    return hashlib.sha256(str(senha).encode("utf-8")).hexdigest()


def garantir_schema_admin():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            nome_fantasia TEXT,
            cnpj_cpf TEXT NOT NULL,
            email TEXT,
            telefone TEXT,
            senha_hash TEXT,
            plano TEXT DEFAULT '7 Dias Grátis',
            status_assinatura TEXT DEFAULT 'Teste',
            periodo_assinatura TEXT DEFAULT '7 dias grátis',
            data_inicio_assinatura TEXT DEFAULT CURRENT_TIMESTAMP,
            data_fim_assinatura TEXT,
            motivo_bloqueio TEXT,
            observacao_admin TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    colunas = {
        "nome_fantasia": "TEXT",
        "plano": "TEXT DEFAULT '7 Dias Grátis'",
        "status_assinatura": "TEXT DEFAULT 'Teste'",
        "periodo_assinatura": "TEXT DEFAULT '7 dias grátis'",
        "data_inicio_assinatura": "TEXT DEFAULT CURRENT_TIMESTAMP",
        "data_fim_assinatura": "TEXT",
        "motivo_bloqueio": "TEXT",
        "observacao_admin": "TEXT",
    }

    cur.execute("PRAGMA table_info(empresas)")
    existentes = [c[1] for c in cur.fetchall()]

    for coluna, tipo in colunas.items():
        if coluna not in existentes:
            cur.execute(f"ALTER TABLE empresas ADD COLUMN {coluna} {tipo}")

    conn.commit()
    conn.close()


def autenticar_master():
    senha_admin = os.getenv("GOIA_ADMIN_PASSWORD", "").strip()

    if not senha_admin:
        st.error("Variável GOIA_ADMIN_PASSWORD não configurada no Render.")
        st.stop()

    if st.session_state.get("goia_admin_logado"):
        return

    st.markdown("""
    <div class="admin-login-card">
        <div class="admin-badge">🛡️ Área Master</div>
        <div class="admin-title">GOIA Control Center</div>
        <div class="admin-subtitle">
            Painel Master para gestão de assinantes, planos, permissões, financeiro, auditoria e operação.
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_admin"):
        senha = st.text_input("🔒 Senha Master", type="password")
        entrar = st.form_submit_button("Entrar no Control Center", use_container_width=True)

    if entrar:
        if senha.strip() == senha_admin:
            st.session_state["goia_admin_logado"] = True
            st.rerun()
        else:
            st.error("Senha master inválida. Verifique a variável GOIA_ADMIN_PASSWORD no Render.")

    st.stop()


def carregar_empresas():
    conn = conectar()
    df = pd.read_sql_query("""
        SELECT
            id,
            nome,
            nome_fantasia,
            cnpj_cpf,
            email,
            telefone,
            plano,
            status_assinatura,
            periodo_assinatura,
            data_inicio_assinatura,
            data_fim_assinatura,
            criado_em
        FROM empresas
        ORDER BY id DESC
    """, conn)
    conn.close()
    return df


def contar_tabela(tabela):
    conn = conectar()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT COUNT(*) FROM {tabela}")
        total = cur.fetchone()[0] or 0
    except Exception:
        total = 0
    conn.close()
    return total


def atualizar_assinante(empresa_id, plano, status, data_fim, observacao):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        UPDATE empresas
        SET plano = ?,
            status_assinatura = ?,
            data_fim_assinatura = ?,
            observacao_admin = ?
        WHERE id = ?
    """, (plano, status, data_fim, observacao, empresa_id))
    conn.commit()
    conn.close()


def resetar_senha(empresa_id, nova_senha):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        UPDATE empresas
        SET senha_hash = ?
        WHERE id = ?
    """, (hash_senha(nova_senha), empresa_id))
    conn.commit()
    conn.close()


def excluir_empresa(empresa_id):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM empresas WHERE id = ?", (empresa_id,))
    conn.commit()
    conn.close()


aplicar_estilo_admin()
garantir_schema_admin()
autenticar_master()

st.sidebar.markdown("## Admin GOIA")
st.sidebar.caption("Navegação")

pagina = st.sidebar.radio(
    "Menu",
    ["Dashboard Master", "Assinantes", "Ações administrativas", "Zona de risco"],
    label_visibility="collapsed"
)

if st.sidebar.button("Sair do Admin"):
    st.session_state.pop("goia_admin_logado", None)
    st.rerun()

empresas = carregar_empresas()

st.markdown("""
<div class="admin-hero">
    <small>GOIA Finance Platform</small>
    <h1>GOIA Control Center</h1>
    <p>Centro de controle da plataforma GOIA. Gerencie assinantes, planos, permissões, auditoria, faturamento e operação.</p>
</div>
""", unsafe_allow_html=True)

if pagina == "Dashboard Master":
    total = len(empresas)
    ativos = len(empresas[empresas["status_assinatura"].fillna("") == "Ativa"])
    testes = len(empresas[empresas["status_assinatura"].fillna("") == "Teste"])
    suspensos = len(empresas[empresas["status_assinatura"].fillna("") == "Suspensa"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Assinantes", total)
    c2.metric("Ativos", ativos)
    c3.metric("Em teste", testes)
    c4.metric("Suspensos", suspensos)

    st.divider()

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Documentos", contar_tabela("documentos"))
    c6.metric("Clientes", contar_tabela("clientes"))
    c7.metric("Fornecedores", contar_tabela("fornecedores"))
    c8.metric("Processos", contar_tabela("processos_documentais"))

    st.subheader("Últimos assinantes")

    if empresas.empty:
        st.info("Nenhum assinante cadastrado.")
    else:
        st.dataframe(empresas.head(10), width="stretch", hide_index=True)

elif pagina == "Assinantes":
    st.subheader("Assinantes cadastrados")

    busca = st.text_input("Buscar por nome, CNPJ, e-mail ou telefone")

    df = empresas.copy()

    if busca.strip() and not df.empty:
        termo = busca.strip().lower()
        df = df[
            df.astype(str).apply(
                lambda linha: linha.str.lower().str.contains(termo, na=False).any(),
                axis=1
            )
        ]

    if df.empty:
        st.info("Nenhum assinante encontrado.")
    else:
        st.dataframe(df, width="stretch", hide_index=True)

elif pagina == "Ações administrativas":
    st.subheader("Editar assinante")

    if empresas.empty:
        st.info("Nenhum assinante cadastrado.")
        st.stop()

    opcoes = empresas.apply(
        lambda r: f"{r['id']} | {r['nome']} | {r['cnpj_cpf']}",
        axis=1
    ).tolist()

    selecionado = st.selectbox("Selecionar assinante", opcoes)
    empresa_id = int(selecionado.split("|")[0].strip())

    col1, col2 = st.columns(2)

    with col1:
        plano = st.selectbox(
            "Plano",
            ["7 Dias Grátis", "Mensal", "Trimestral", "Semestral", "Anual", "VIP", "Indeterminado"]
        )

        status = st.selectbox(
            "Status",
            ["Teste", "Ativa", "VIP", "Suspensa", "Bloqueada", "Inativa"]
        )

        data_fim = st.text_input("Data fim assinatura", placeholder="AAAA-MM-DD ou deixe em branco")
        observacao = st.text_area("Observação administrativa")

        if st.button("Salvar alterações", use_container_width=True):
            atualizar_assinante(empresa_id, plano, status, data_fim, observacao)
            st.success("Assinante atualizado.")
            st.rerun()

    with col2:
        nova_senha = st.text_input("Nova senha do assinante", type="password")

        if st.button("Resetar senha", use_container_width=True):
            if not nova_senha:
                st.error("Informe a nova senha.")
            else:
                resetar_senha(empresa_id, nova_senha)
                st.success("Senha redefinida.")

else:
    st.subheader("Zona de risco")

    if empresas.empty:
        st.info("Nenhum assinante cadastrado.")
        st.stop()

    opcoes = empresas.apply(
        lambda r: f"{r['id']} | {r['nome']} | {r['cnpj_cpf']}",
        axis=1
    ).tolist()

    selecionado = st.selectbox("Selecionar assinante para exclusão", opcoes)
    empresa_id = int(selecionado.split("|")[0].strip())

    st.warning("Excluir remove a empresa da tabela empresas. Prefira Suspensa ou Bloqueada quando possível.")

    confirmacao = st.text_input(f"Digite EXCLUIR {empresa_id} para confirmar")

    if st.button("Excluir definitivamente"):
        if confirmacao == f"EXCLUIR {empresa_id}":
            excluir_empresa(empresa_id)
            st.success("Assinante excluído.")
            st.rerun()
        else:
            st.error("Confirmação inválida.")

st.caption("GOIA · Área Master da plataforma")
