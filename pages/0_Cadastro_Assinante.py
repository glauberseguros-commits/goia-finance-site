import hashlib
import re
import sqlite3
from pathlib import Path

import streamlit as st
from utils.ui import aplicar_estilo_premium
from utils.padronizadores import limpar_cnpj, limpar_telefone, telefone_valido

DB_PATH = Path("bd/gofinance.db")


st.set_page_config(
    page_title="Cadastro de Assinante",
    page_icon="🏢",
    layout="wide"
)

aplicar_estilo_premium()


def conectar():
    return sqlite3.connect(DB_PATH)


def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def preparar_banco():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL
    )
    """)

    cur.execute("PRAGMA table_info(empresas)")
    cols = [c[1] for c in cur.fetchall()]

    def add_col(nome, tipo):
        if nome not in cols:
            cur.execute(f"ALTER TABLE empresas ADD COLUMN {nome} {tipo}")

    add_col("cnpj_cpf", "TEXT")
    add_col("nome_fantasia", "TEXT")
    add_col("admin_nome", "TEXT")
    add_col("email", "TEXT")
    add_col("telefone", "TEXT")
    add_col("senha_hash", "TEXT")
    add_col("plano", "TEXT DEFAULT 'Teste'")
    add_col("status_assinatura", "TEXT DEFAULT 'Ativa'")
    add_col("criado_em", "TEXT DEFAULT CURRENT_TIMESTAMP")

    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_empresas_cnpj_cpf_unico
    ON empresas(cnpj_cpf)
    WHERE cnpj_cpf IS NOT NULL AND cnpj_cpf <> ''
    """)

    conn.commit()
    conn.close()


def cnpj_valido_basico(cnpj):
    numeros = limpar_cnpj(cnpj)
    return len(numeros) == 14


def email_valido(email):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""))


def empresa_existe(cnpj):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    SELECT id, nome
    FROM empresas
    WHERE REPLACE(REPLACE(REPLACE(REPLACE(cnpj_cpf,'.',''),'/',''),'-',''),' ','') = ?
    LIMIT 1
    """, (limpar_cnpj(cnpj),))

    row = cur.fetchone()
    conn.close()

    return row


def criar_empresa(cnpj, razao, fantasia, nome_admin, email, telefone, senha):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO empresas (
        nome,
        cnpj_cpf,
        nome_fantasia,
        admin_nome,
        email,
        telefone,
        senha_hash,
        plano,
        status_assinatura
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        razao.strip(),
        limpar_cnpj(cnpj),
        fantasia.strip(),
        nome_admin.strip(),
        email.strip().lower(),
        limpar_telefone(telefone),
        hash_senha(senha),
        "Teste",
        "Ativa"
    ))

    empresa_id = cur.lastrowid

    conn.commit()
    conn.close()

    return empresa_id


def menu_publico():
    st.sidebar.markdown("## GOIA")
    st.sidebar.page_link("app.py", label="Já tenho conta", icon="🔐")
    st.sidebar.page_link("pages/0_Cadastro_Assinante.py", label="Criar conta", icon="🏢")


preparar_banco()
menu_publico()

if st.session_state.get("logado") and st.session_state.get("empresa_id"):
    st.success("Você já está logado na GOIA.")
    if st.button("Ir para o Dashboard"):
        st.switch_page("app.py")
    st.stop()


st.title("🏢 Criar Conta GOIA")
st.caption("Cadastre sua empresa para utilizar a plataforma.")

with st.container(border=True):
    with st.form("cadastro_empresa"):
        cnpj = st.text_input("CNPJ")
        razao = st.text_input("Razão Social")
        fantasia = st.text_input("Nome Fantasia")

        nome_admin = st.text_input("Nome do Administrador")
        email = st.text_input("E-mail")
        telefone = st.text_input("Telefone / WhatsApp")

        senha = st.text_input("Senha", type="password")
        confirmar = st.text_input("Confirmar Senha", type="password")

        enviar = st.form_submit_button("Criar Conta")

if enviar:
    if not cnpj_valido_basico(cnpj):
        st.error("Informe um CNPJ válido com 14 dígitos.")

    elif not razao.strip():
        st.error("Informe a Razão Social.")

    elif not nome_admin.strip():
        st.error("Informe o nome do administrador.")

    elif not email_valido(email):
        st.error("Informe um e-mail válido.")

    elif not telefone_valido(telefone):
        st.error("Telefone inválido. Informe DDD + número.")

    elif not senha:
        st.error("Informe uma senha.")

    elif senha != confirmar:
        st.error("As senhas não conferem.")

    elif empresa_existe(cnpj):
        st.warning("Este CNPJ já possui cadastro. Use a opção 'Já tenho conta'.")

    else:
        empresa_id = criar_empresa(
            cnpj,
            razao,
            fantasia,
            nome_admin,
            email,
            telefone,
            senha
        )

        st.session_state["logado"] = True
        st.session_state["empresa_id"] = empresa_id
        st.session_state["empresa_nome"] = razao.strip()

        st.success("Conta criada com sucesso. Entrando na GOIA...")
        st.rerun()