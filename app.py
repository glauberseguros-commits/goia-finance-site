import sqlite3
import hashlib
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path("bd/gofinance.db")
CSV_PATH = Path("dados/financeiro.csv")

st.set_page_config(
    page_title="GOIA Finance Platform",
    page_icon="💰",
    layout="wide"
)

def conectar():
    return sqlite3.connect(DB_PATH)

def limpar_doc(valor):
    return "".join(filter(str.isdigit, valor or ""))

def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

def data_br(valor):
    if not valor:
        return ""
    try:
        return pd.to_datetime(valor).strftime("%d/%m/%Y")
    except Exception:
        return valor

def garantir_coluna(tabela, coluna, tipo):
    conn = conectar()
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({tabela})")
    cols = [c[1] for c in cur.fetchall()]
    if coluna not in cols:
        cur.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")
    conn.commit()
    conn.close()

def preparar_auth():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cnpj_cpf TEXT,
        email TEXT,
        telefone TEXT,
        plano TEXT DEFAULT 'Teste',
        status_assinatura TEXT DEFAULT 'Ativa',
        data_inicio TEXT DEFAULT CURRENT_DATE,
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

    garantir_coluna("empresas", "senha_hash", "TEXT")
    garantir_coluna("empresas", "tipo_conta", "TEXT DEFAULT 'Assinante'")

preparar_auth()

def buscar_empresa_login(cnpj, senha):
    cnpj_limpo = limpar_doc(cnpj)

    conn = conectar()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nome, cnpj_cpf, plano, status_assinatura
        FROM empresas
        WHERE REPLACE(REPLACE(REPLACE(REPLACE(cnpj_cpf,'.',''),'/',''),'-',''),' ','') = ?
          AND senha_hash = ?
          AND COALESCE(status_assinatura, 'Ativa') = 'Ativa'
        LIMIT 1
    """, (cnpj_limpo, hash_senha(senha)))

    row = cur.fetchone()
    conn.close()

    return dict(row) if row else None

def criar_empresa(nome, cnpj, email, telefone, senha):
    cnpj_limpo = limpar_doc(cnpj)

    if not cnpj_limpo:
        return False, "Informe um CNPJ válido."

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id FROM empresas
        WHERE REPLACE(REPLACE(REPLACE(REPLACE(cnpj_cpf,'.',''),'/',''),'-',''),' ','') = ?
    """, (cnpj_limpo,))

    if cur.fetchone():
        conn.close()
        return False, "Este CNPJ já está cadastrado."

    cur.execute("""
        INSERT INTO empresas (
            nome, cnpj_cpf, email, telefone, senha_hash,
            plano, status_assinatura, tipo_conta, data_inicio
        )
        VALUES (?, ?, ?, ?, ?, 'Teste', 'Ativa', 'Assinante', date('now'))
    """, (
        nome.strip(),
        cnpj.strip(),
        email.strip(),
        telefone.strip(),
        hash_senha(senha)
    ))

    conn.commit()
    conn.close()

    return True, "Empresa cadastrada com sucesso. Agora faça login."

def tela_login():
    if st.session_state.get("logado") and st.session_state.get("empresa_id"):
        return

    st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="stHeader"] {background: transparent;}
        
.block-container {max-width: 1180px; padding-top: 55px;}

div[data-baseweb="input"] > div {
    background-color: #ffffff !important;
    border: 1.5px solid #94a3b8 !important;
    border-radius: 10px !important;
}

input {
    color: #0f172a !important;
    font-weight: 600 !important;
}

label {
    color: #1e293b !important;
    font-weight: 700 !important;
}

button[kind="secondary"], button[kind="primary"] {
    border-radius: 10px !important;
    border: 1px solid #111827 !important;
    font-weight: 700 !important;
}

.stTabs [data-baseweb="tab"] {
    font-weight: 700 !important;
}

        .login-hero {
            background: linear-gradient(135deg, #050816 0%, #111827 55%, #172554 100%);
            border-radius: 28px;
            padding: 48px;
            color: white;
            margin-bottom: 28px;
            box-shadow: 0 24px 70px rgba(15, 23, 42, 0.22);
        }
        .login-kicker {
            color: #2dd4bf;
            font-size: 13px;
            font-weight: 800;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            margin-bottom: 12px;
        }
        .login-title {
            font-size: 44px;
            font-weight: 900;
            line-height: 1.08;
            margin-bottom: 16px;
        }
        .login-text {
            color: #cbd5e1;
            font-size: 17px;
            max-width: 760px;
        }
    </style>
    <div class="login-hero">
        <div class="login-kicker">GOIA Finance Platform</div>
        <div class="login-title">Inteligência financeira para empresas document-driven.</div>
        <div class="login-text">
            Entre com o CNPJ da empresa ou crie uma conta para cadastrar sua empresa na GOIA.
        </div>
    </div>
    """, unsafe_allow_html=True)

    aba1, aba2 = st.tabs(["Entrar", "Criar conta"])

    with aba1:
        st.subheader("Entrar na GOIA")

        with st.form("form_login"):
            cnpj = st.text_input("CNPJ")
            senha = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar")

        if entrar:
            empresa = buscar_empresa_login(cnpj, senha)

            if not empresa:
                st.error("CNPJ ou senha inválidos.")
                st.stop()

            st.session_state["logado"] = True
            st.session_state["empresa_id"] = empresa["id"]
            st.session_state["empresa_nome"] = empresa["nome"]
            st.rerun()

    with aba2:
        st.subheader("Cadastrar empresa assinante")

        with st.form("form_cadastro"):
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
            elif not nome or not cnpj or not senha:
                st.error("Preencha empresa, CNPJ e senha.")
            else:
                ok, msg = criar_empresa(nome, cnpj, email, telefone, senha)
                st.success(msg) if ok else st.warning(msg)

    st.stop()

tela_login()

EMPRESA_ID = st.session_state["empresa_id"]

def carregar_movimentacoes():
    conn = conectar()

    try:
        receber = pd.read_sql_query("""
            SELECT data_vencimento AS data, 'Receber' AS tipo, descricao, categoria, valor, status
            FROM contas_receber
            WHERE empresa_id = ?
        """, conn, params=(EMPRESA_ID,))
    except Exception:
        receber = pd.DataFrame(columns=["data", "tipo", "descricao", "categoria", "valor", "status"])

    try:
        pagar = pd.read_sql_query("""
            SELECT data_vencimento AS data, 'Pagar' AS tipo, descricao, categoria, -valor AS valor, status
            FROM contas_pagar
            WHERE empresa_id = ?
        """, conn, params=(EMPRESA_ID,))
    except Exception:
        pagar = pd.DataFrame(columns=["data", "tipo", "descricao", "categoria", "valor", "status"])

    conn.close()
    return pd.concat([receber, pagar], ignore_index=True)

def contar_pendencias():
    conn = conectar()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*)
            FROM processo_pendencias
            WHERE empresa_id = ?
              AND status = 'Pendente'
        """, (EMPRESA_ID,))
        total = cur.fetchone()[0]
    except Exception:
        total = 0
    conn.close()
    return total

st.sidebar.markdown("## GOIA")
st.sidebar.caption(st.session_state.get("empresa_nome", "Empresa"))

if st.sidebar.button("Sair"):
    st.session_state.clear()
    st.rerun()

st.sidebar.page_link("app.py", label="Dashboard", icon="🏠")
st.sidebar.page_link("pages/1_Importar_Documento.py", label="Importar Documento", icon="📄")
st.sidebar.page_link("pages/9_Clientes.py", label="Clientes", icon="👥")
st.sidebar.page_link("pages/10_Fornecedores.py", label="Fornecedores", icon="🏭")
st.sidebar.page_link("pages/2_Contas_a_Receber.py", label="Contas a Receber", icon="💰")
st.sidebar.page_link("pages/3_Contas_a_Pagar.py", label="Contas a Pagar", icon="💸")
st.sidebar.page_link("pages/4_Compras.py", label="Compras", icon="🛒")
st.sidebar.page_link("pages/5_Produtos_Estoque.py", label="Produtos Estoque", icon="📦")
st.sidebar.page_link("pages/6_Vendas.py", label="Vendas", icon="🧾")
st.sidebar.page_link("pages/7_Processos_Documentais.py", label="Processos Documentais", icon="🗂️")
st.sidebar.page_link("pages/8_Conciliacao_Bancaria.py", label="Conciliação Bancária", icon="🏦")

df = carregar_movimentacoes()

recebimentos = df[df["tipo"] == "Receber"]["valor"].sum() if not df.empty else 0
pagamentos = abs(df[df["tipo"] == "Pagar"]["valor"].sum()) if not df.empty else 0
saldo = recebimentos - pagamentos
pendencias = contar_pendencias()

st.title("💰 GOIA Finance Platform")
st.caption(f"Empresa ativa: {st.session_state.get('empresa_nome')}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Recebimentos", moeda(recebimentos))
with col2:
    st.metric("Pagamentos", moeda(pagamentos))
with col3:
    st.metric("Saldo operacional", moeda(saldo))
with col4:
    st.metric("Pendências", pendencias)

st.divider()

st.subheader("Módulos principais")

m1, m2, m3, m4 = st.columns(4)

with m1:
    with st.container(border=True):
        st.markdown("### 👥 Clientes")
        st.write("Cadastro, notas emitidas e contas a receber.")
        st.page_link("pages/9_Clientes.py", label="Acessar Clientes")

with m2:
    with st.container(border=True):
        st.markdown("### 🏭 Fornecedores")
        st.write("Cadastro, notas recebidas e contas a pagar.")
        st.page_link("pages/10_Fornecedores.py", label="Acessar Fornecedores")

with m3:
    with st.container(border=True):
        st.markdown("### 📄 Importar Documento")
        st.write("NF-e, PDF, XML, CSV, comprovantes e extratos.")
        st.page_link("pages/1_Importar_Documento.py", label="Acessar Importação")

with m4:
    with st.container(border=True):
        st.markdown("### 🏦 Conciliação")
        st.write("Banco, contas, documentos e baixas.")
        st.page_link("pages/8_Conciliacao_Bancaria.py", label="Acessar Conciliação")

st.divider()

st.subheader("Movimentações financeiras")

if df.empty:
    st.info("Nenhuma movimentação encontrada para esta empresa.")
else:
    df_view = df.copy()
    df_view["data"] = df_view["data"].apply(data_br)
    df_view["valor"] = df_view["valor"].apply(moeda)
    st.dataframe(df_view, width="stretch", hide_index=True)

st.caption("GOIA Finance Platform · SaaS multiempresa")
