import sqlite3
import hashlib
from pathlib import Path
import pandas as pd
import streamlit as st

DB_PATH = Path("bd/gofinance.db")

st.set_page_config(
    page_title="GOIA Finance Platform",
    page_icon="💰",
    layout="wide"
)

def conectar():
    return sqlite3.connect(DB_PATH)

def limpar_doc(v):
    return "".join(filter(str.isdigit, v or ""))

def hash_senha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def moeda(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def preparar_banco():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cnpj_cpf TEXT,
        email TEXT,
        telefone TEXT,
        senha_hash TEXT,
        plano TEXT DEFAULT 'Teste',
        status_assinatura TEXT DEFAULT 'Ativa',
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def buscar_empresa(cnpj, senha):
    conn = conectar()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
    SELECT id, nome, cnpj_cpf
    FROM empresas
    WHERE REPLACE(REPLACE(REPLACE(REPLACE(cnpj_cpf,'.',''),'/',''),'-',''),' ','') = ?
      AND senha_hash = ?
      AND COALESCE(status_assinatura, 'Ativa') = 'Ativa'
    LIMIT 1
    """, (limpar_doc(cnpj), hash_senha(senha)))

    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def criar_empresa(nome, cnpj, email, telefone, senha):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    SELECT id FROM empresas
    WHERE REPLACE(REPLACE(REPLACE(REPLACE(cnpj_cpf,'.',''),'/',''),'-',''),' ','') = ?
    """, (limpar_doc(cnpj),))

    if cur.fetchone():
        conn.close()
        return False, "CNPJ já cadastrado."

    cur.execute("""
    INSERT INTO empresas (nome, cnpj_cpf, email, telefone, senha_hash)
    VALUES (?, ?, ?, ?, ?)
    """, (nome, cnpj, email, telefone, hash_senha(senha)))

    conn.commit()
    conn.close()
    return True, "Empresa cadastrada. Agora entre na GOIA."

def tela_login():
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {display:none;}
    .block-container {max-width:1100px; padding-top:55px;}
    .hero {
        background:linear-gradient(135deg,#050816,#172554);
        color:white; padding:46px; border-radius:28px;
        box-shadow:0 22px 60px rgba(15,23,42,.22);
        margin-bottom:26px;
    }
    .kicker {color:#2dd4bf; font-weight:800; letter-spacing:.18em; font-size:13px;}
    .title {font-size:42px; font-weight:900; line-height:1.08; margin-top:16px;}
    .text {color:#cbd5e1; font-size:17px; margin-top:18px;}
    .stTextInput input {
        background:#fff !important;
        border:2px solid #334155 !important;
        color:#0f172a !important;
        font-weight:700 !important;
    }
    .stButton button {
        background:#111827 !important;
        color:white !important;
        border-radius:10px !important;
        font-weight:800 !important;
    }
    </style>

    <div class="hero">
      <div class="kicker">GOIA FINANCE PLATFORM</div>
      <div class="title">Inteligência financeira para empresas document-driven.</div>
      <div class="text">Entre com o CNPJ da empresa ou crie sua conta para iniciar.</div>
    </div>
    """, unsafe_allow_html=True)

    aba_login, aba_cadastro = st.tabs(["Já tenho conta", "Criar conta"])

    with aba_login:
        st.subheader("Entrar na GOIA")
        with st.form("login"):
            cnpj = st.text_input("CNPJ")
            senha = st.text_input("Senha", type="password")
            acessar = st.form_submit_button("Entrar na GOIA")

        if acessar:
            empresa = buscar_empresa(cnpj, senha)
            if not empresa:
                st.error("CNPJ ou senha inválidos.")
                st.stop()

            st.session_state["logado"] = True
            st.session_state["empresa_id"] = empresa["id"]
            st.session_state["empresa_nome"] = empresa["nome"]
            st.rerun()

    with aba_cadastro:
        st.subheader("Cadastrar empresa")
        with st.form("cadastro"):
            nome = st.text_input("Razão Social / Nome da empresa")
            cnpj = st.text_input("CNPJ")
            email = st.text_input("E-mail")
            telefone = st.text_input("Telefone")
            senha = st.text_input("Senha", type="password")
            confirmar = st.text_input("Confirmar senha", type="password")
            criar = st.form_submit_button("Criar conta")

        if criar:
            if senha != confirmar:
                st.error("As senhas não conferem.")
            elif not email.strip() or not telefone.strip() or not senha:
                st.error("Informe e-mail, telefone e senha.")
            else:
                ok, msg = criar_empresa(nome, cnpj, email, telefone, senha)
                st.success(msg) if ok else st.warning(msg)

    st.stop()

preparar_banco()

if not st.session_state.get("logado") or not st.session_state.get("empresa_id"):
    tela_login()
    st.stop()

EMPRESA_ID = st.session_state.get("empresa_id")

def carregar_movimentacoes():
    conn = conectar()

    try:
        receber = pd.read_sql_query("""
            SELECT data_vencimento AS data, 'Receber' AS tipo, descricao, categoria, valor, status
            FROM contas_receber
            WHERE empresa_id = ?
        """, conn, params=(EMPRESA_ID,))
    except:
        receber = pd.DataFrame(columns=["data", "tipo", "descricao", "categoria", "valor", "status"])

    try:
        pagar = pd.read_sql_query("""
            SELECT data_vencimento AS data, 'Pagar' AS tipo, descricao, categoria, -valor AS valor, status
            FROM contas_pagar
            WHERE empresa_id = ?
        """, conn, params=(EMPRESA_ID,))
    except:
        pagar = pd.DataFrame(columns=["data", "tipo", "descricao", "categoria", "valor", "status"])

    conn.close()
    return pd.concat([receber, pagar], ignore_index=True)

df = carregar_movimentacoes()

recebimentos = df[df["tipo"] == "Receber"]["valor"].sum() if not df.empty else 0
pagamentos = abs(df[df["tipo"] == "Pagar"]["valor"].sum()) if not df.empty else 0
saldo = recebimentos - pagamentos

st.sidebar.markdown("## GOIA")
st.sidebar.caption(st.session_state.get("empresa_nome"))

if st.sidebar.button("Sair"):
    st.session_state.clear()
    st.rerun()

st.sidebar.page_link("app.py", label="Dashboard", icon="🏠")
st.sidebar.page_link("pages/1_Importar_Documento.py", label="Importar Documento", icon="📄")
st.sidebar.page_link("pages/9_Clientes.py", label="Clientes", icon="👥")
st.sidebar.page_link("pages/10_Fornecedores.py", label="Fornecedores", icon="🏭")
st.sidebar.page_link("pages/2_Contas_a_Receber.py", label="Contas a Receber", icon="💰")
st.sidebar.page_link("pages/3_Contas_a_Pagar.py", label="Contas a Pagar", icon="💸")

st.title("💰 GOIA Finance Platform")
st.caption(f"Empresa ativa: {st.session_state.get('empresa_nome')}")

c1, c2, c3 = st.columns(3)
c1.metric("Recebimentos", moeda(recebimentos))
c2.metric("Pagamentos", moeda(pagamentos))
c3.metric("Saldo operacional", moeda(saldo))

st.divider()
st.subheader("Movimentações financeiras")

if df.empty:
    st.info("Nenhuma movimentação encontrada para esta empresa.")
else:
    st.dataframe(df, width="stretch", hide_index=True)
