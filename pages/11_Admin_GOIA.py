
import os
import hashlib
import pandas as pd
import streamlit as st

from utils.db import conectar_banco
from utils.ui import aplicar_estilo_premium
from utils.premium import aplicar_premium_goia, hero

st.set_page_config(
    page_title="Admin GOIA",
    page_icon="🛡️",
    layout="wide"
)

aplicar_estilo_premium()
aplicar_premium_goia()

def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def autenticar_master():
    senha_admin = os.getenv("GOIA_ADMIN_PASSWORD", "").strip()

    if not senha_admin:
        st.error("Variável GOIA_ADMIN_PASSWORD não configurada no Render.")
        st.stop()

    if st.session_state.get("goia_admin_logado"):
        return

    st.title("🛡️ Admin GOIA")
    st.caption("Área restrita ao dono da plataforma.")

    senha = st.text_input("Senha master GOIA", type="password")

    if st.button("Entrar no Admin"):
        if senha == senha_admin:
            st.session_state["goia_admin_logado"] = True
            st.rerun()
        else:
            st.error("Senha master inválida.")

    st.stop()

def carregar_empresas():
    conn = conectar_banco()

    df = pd.read_sql_query("""
        SELECT
            id,
            nome,
            cnpj_cpf,
            email,
            telefone,
            plano,
            status_assinatura,
            criado_em
        FROM empresas
        ORDER BY id DESC
    """, conn)

    conn.close()
    return df

def atualizar_status(empresa_id, status):
    conn = conectar_banco()
    cur = conn.cursor()

    cur.execute("""
        UPDATE empresas
        SET status_assinatura = ?
        WHERE id = ?
    """, (status, empresa_id))

    conn.commit()
    conn.close()

def resetar_senha(empresa_id, nova_senha):
    conn = conectar_banco()
    cur = conn.cursor()

    cur.execute("""
        UPDATE empresas
        SET senha_hash = ?
        WHERE id = ?
    """, (hash_senha(nova_senha), empresa_id))

    conn.commit()
    conn.close()

def excluir_empresa(empresa_id):
    conn = conectar_banco()
    cur = conn.cursor()

    cur.execute("DELETE FROM empresas WHERE id = ?", (empresa_id,))

    conn.commit()
    conn.close()

autenticar_master()

hero(
    "Admin GOIA",
    "Gestão master de assinantes, bloqueios, liberações e controle operacional da plataforma.",
    icone="GOIA"
)

if st.sidebar.button("Sair do Admin"):
    st.session_state.pop("goia_admin_logado", None)
    st.rerun()

empresas = carregar_empresas()

total = len(empresas)
ativas = len(empresas[empresas["status_assinatura"].fillna("Ativa") == "Ativa"])
bloqueadas = len(empresas[empresas["status_assinatura"].fillna("") == "Bloqueada"])

c1, c2, c3 = st.columns(3)
c1.metric("Assinantes", total)
c2.metric("Ativos", ativas)
c3.metric("Bloqueados", bloqueadas)

st.divider()

st.subheader("Assinantes cadastrados")

if empresas.empty:
    st.info("Nenhum assinante cadastrado.")
    st.stop()

st.dataframe(empresas, width="stretch", hide_index=True)

st.divider()

st.subheader("Ações administrativas")

empresa_opcao = st.selectbox(
    "Selecionar assinante",
    empresas.apply(lambda r: f"{r['id']} | {r['nome']} | {r['cnpj_cpf']}", axis=1).tolist()
)

empresa_id = int(empresa_opcao.split("|")[0].strip())

col1, col2 = st.columns(2)

with col1:
    novo_status = st.selectbox(
        "Status do assinante",
        ["Ativa", "Bloqueada", "Suspensa", "Inativa"]
    )

    if st.button("Atualizar status"):
        atualizar_status(empresa_id, novo_status)
        st.success("Status atualizado.")
        st.rerun()

with col2:
    nova_senha = st.text_input("Nova senha do assinante", type="password")

    if st.button("Resetar senha"):
        if not nova_senha:
            st.error("Informe a nova senha.")
        else:
            resetar_senha(empresa_id, nova_senha)
            st.success("Senha redefinida.")

st.divider()

with st.expander("Zona de risco: excluir assinante"):
    st.warning("Excluir remove a empresa da tabela empresas. Use preferencialmente Bloqueada ou Inativa.")

    confirmacao = st.text_input(f"Digite EXCLUIR {empresa_id} para confirmar")

    if st.button("Excluir definitivamente"):
        if confirmacao == f"EXCLUIR {empresa_id}":
            excluir_empresa(empresa_id)
            st.success("Assinante excluído.")
            st.rerun()
        else:
            st.error("Confirmação inválida.")

st.caption("Área Master GOIA · Uso restrito ao proprietário da plataforma.")
