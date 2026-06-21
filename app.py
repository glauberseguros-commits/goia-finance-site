import sqlite3
import hashlib
import re
from pathlib import Path
from io import BytesIO
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
    return True, "Empresa cadastrada. Agora acesse o sistema."


def formatar_cnpj(valor):
    n = limpar_doc(valor)
    if len(n) == 14:
        return f"{n[:2]}.{n[2:5]}.{n[5:8]}/{n[8:12]}-{n[12:]}"
    return valor or ""

def limpar_espacos_ocr(valor):
    if not valor:
        return ""
    if valor.count(" ") >= max(3, len(valor) // 4):
        return valor.replace(" ", "").strip()
    return valor.strip()

def valor_apos_rotulo(texto, rotulo):
    linhas = [x.strip() for x in texto.splitlines() if x.strip()]
    for i, linha in enumerate(linhas):
        if linha.upper() == rotulo.upper() and i + 1 < len(linhas):
            return limpar_espacos_ocr(linhas[i + 1])
    return ""

def extrair_dados_cartao_cnpj_pdf(arquivo):
    dados = {"nome": "", "cnpj": "", "email": "", "telefone": ""}

    try:
        from pypdf import PdfReader
        arquivo.seek(0)
        reader = PdfReader(BytesIO(arquivo.read()))
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() or ""
            texto += "\n"
    except Exception:
        return dados

    nome = valor_apos_rotulo(texto, "NOME EMPRESARIAL")
    cnpj = ""

    texto_sem_espacos = re.sub(r"\s+", "", texto)
    m = re.search(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}", texto_sem_espacos)
    if m:
        cnpj = formatar_cnpj(m.group())

    texto_normal = re.sub(r"\s+", " ", texto)

    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", texto_normal)
    if email_match:
        dados["email"] = email_match.group()

    tel_match = re.search(r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}", texto_normal)
    if tel_match:
        dados["telefone"] = tel_match.group()

    dados["nome"] = nome
    dados["cnpj"] = cnpj
    return dados


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
        st.subheader("Acessar sistema")
        with st.form("login"):
            cnpj = st.text_input("CNPJ")
            senha = st.text_input("Senha", type="password")
            acessar = st.form_submit_button("Acessar sistema")

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

        st.caption("Primeiro anexe o Cartão CNPJ oficial. A GOIA preencherá Razão Social e CNPJ a partir do documento.")

        documento_empresa = st.file_uploader(
            "Anexar Cartão CNPJ / documento oficial da empresa",
            type=["pdf"],
            key="documento_cadastro_empresa"
        )

        dados_doc = {"nome": "", "cnpj": "", "email": "", "telefone": ""}

        if not documento_empresa:
            st.warning("Anexe o Cartão CNPJ para liberar o cadastro.")
        else:
            dados_doc = extrair_dados_cartao_cnpj_pdf(documento_empresa)

            if dados_doc.get("nome") and dados_doc.get("cnpj"):
                st.success(f"Documento lido: {documento_empresa.name}")
            else:
                st.error("Documento anexado, mas não foi possível identificar Razão Social e CNPJ. Envie o Cartão CNPJ oficial em PDF.")

        documento_valido = bool(dados_doc.get("nome")) and bool(dados_doc.get("cnpj"))

        nome_oficial = dados_doc.get("nome", "")
        cnpj_oficial = dados_doc.get("cnpj", "")

        with st.form("cadastro"):
            st.text_input(
                "Razão Social identificada no Cartão CNPJ",
                value=nome_oficial,
                disabled=True
            )

            st.text_input(
                "CNPJ identificado no Cartão CNPJ",
                value=cnpj_oficial,
                disabled=True
            )

            email = st.text_input("E-mail de acesso", value=dados_doc.get("email", ""))
            telefone = st.text_input("Telefone / WhatsApp", value=dados_doc.get("telefone", ""))
            senha = st.text_input("Senha", type="password")
            confirmar = st.text_input("Confirmar senha", type="password")

            criar = st.form_submit_button(
                "Criar conta",
                disabled=not documento_valido
            )

        if criar:
            if not documento_valido:
                st.error("Cadastro bloqueado: anexe o Cartão CNPJ oficial.")
            elif senha != confirmar:
                st.error("As senhas não conferem.")
            elif not email.strip() or not telefone.strip() or not senha:
                st.error("Informe e-mail, telefone e senha.")
            else:
                ok, msg = criar_empresa(nome_oficial, cnpj_oficial, email, telefone, senha)
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
