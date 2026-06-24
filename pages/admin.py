
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

st.markdown("""
<style>
[data-testid="stSidebarNav"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)


def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def autenticar_master():
    senha_admin = os.getenv("GOIA_ADMIN_PASSWORD", "").strip()

    if not senha_admin:
        st.error("GOIA_ADMIN_PASSWORD não configurada no Render.")
        st.stop()

    if st.session_state.get("goia_admin_logado"):
        return

    st.title("🛡️ Admin GOIA")
    st.caption("Área Master do proprietário da plataforma.")

    senha = st.text_input("Senha master", type="password").strip()

    if st.button("Acessar Admin GOIA"):
        if senha == senha_admin:
            st.session_state["goia_admin_logado"] = True
            st.success("Acesso autorizado.")
            st.rerun()
        else:
            st.error("Senha master inválida. Verifique se a senha digitada é exatamente igual à GOIA_ADMIN_PASSWORD do Render.")

    st.stop()


def conectar():
    return conectar_banco()


def garantir_colunas_admin():
    conn = conectar()
    cur = conn.cursor()

    colunas = {
        "plano": "TEXT DEFAULT 'Teste'",
        "status_assinatura": "TEXT DEFAULT 'Ativa'",
        "admin_nome": "TEXT",
        "motivo_bloqueio": "TEXT",
        "observacao_admin": "TEXT",
    }

    cur.execute("PRAGMA table_info(empresas)")
    existentes = [c[1] for c in cur.fetchall()]

    for nome, tipo in colunas.items():
        if nome not in existentes:
            cur.execute(f"ALTER TABLE empresas ADD COLUMN {nome} {tipo}")

    conn.commit()
    conn.close()


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
            admin_nome,
            motivo_bloqueio,
            observacao_admin,
            criado_em
        FROM empresas
        ORDER BY id DESC
    """, conn)

    conn.close()
    return df


def atualizar_status(empresa_id, status, motivo):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        UPDATE empresas
        SET status_assinatura = ?,
            motivo_bloqueio = ?
        WHERE id = ?
    """, (status, motivo, empresa_id))

    conn.commit()
    conn.close()


def atualizar_plano(empresa_id, plano):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        UPDATE empresas
        SET plano = ?
        WHERE id = ?
    """, (plano, empresa_id))

    conn.commit()
    conn.close()


def atualizar_observacao(empresa_id, observacao):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        UPDATE empresas
        SET observacao_admin = ?
        WHERE id = ?
    """, (observacao, empresa_id))

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

    tabelas_com_empresa = [
        "documentos",
        "repositorio_documental",
        "clientes",
        "fornecedores",
        "processos_documentais",
        "processo_pendencias",
        "compras",
        "contas_pagar",
        "vendas",
        "contas_receber",
    ]

    for tabela in tabelas_com_empresa:
        try:
            cur.execute(f"DELETE FROM {tabela} WHERE empresa_id = ?", (empresa_id,))
        except Exception:
            pass

    cur.execute("DELETE FROM empresas WHERE id = ?", (empresa_id,))

    conn.commit()
    conn.close()


def contar_tabela(tabela):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(f"SELECT COUNT(*) FROM {tabela}")
        total = cur.fetchone()[0]
    except Exception:
        total = 0

    conn.close()
    return total


autenticar_master()
garantir_colunas_admin()

st.sidebar.markdown("## Admin GOIA")
pagina = st.sidebar.radio(
    "Navegação",
    [
        "Dashboard Master",
        "Assinantes",
        "Ações administrativas",
        "Zona de risco",
    ],
)

if st.sidebar.button("Sair do Admin"):
    st.session_state.pop("goia_admin_logado", None)
    st.rerun()

hero(
    "Admin GOIA",
    "Área Master para gestão dos assinantes, bloqueios, planos e controle operacional da plataforma.",
    icone="GOIA"
)

empresas = carregar_empresas()

if pagina == "Dashboard Master":
    total = len(empresas)
    ativas = len(empresas[empresas["status_assinatura"].fillna("Ativa") == "Ativa"])
    bloqueadas = len(empresas[empresas["status_assinatura"].fillna("") == "Bloqueada"])
    suspensas = len(empresas[empresas["status_assinatura"].fillna("") == "Suspensa"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Assinantes", total)
    c2.metric("Ativos", ativas)
    c3.metric("Bloqueados", bloqueadas)
    c4.metric("Suspensos", suspensas)

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
        st.dataframe(
            empresas.head(10),
            width="stretch",
            hide_index=True
        )

elif pagina == "Assinantes":
    st.subheader("Assinantes cadastrados")

    busca = st.text_input("Buscar por nome, CNPJ, e-mail ou telefone")

    df = empresas.copy()

    if busca and not df.empty:
        termo = busca.lower()
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
    st.subheader("Bloquear, liberar, suspender, alterar plano e resetar senha")

    if empresas.empty:
        st.info("Nenhum assinante cadastrado.")
        st.stop()

    empresa_opcao = st.selectbox(
        "Selecionar assinante",
        empresas.apply(
            lambda r: f"{r['id']} | {r['nome']} | {r['cnpj_cpf']} | {r['status_assinatura']}",
            axis=1
        ).tolist()
    )

    empresa_id = int(empresa_opcao.split("|")[0].strip())

    empresa_atual = empresas[empresas["id"] == empresa_id].iloc[0]

    st.info(f"Assinante selecionado: {empresa_atual['nome']}")

    col1, col2 = st.columns(2)

    with col1:
        novo_status = st.selectbox(
            "Novo status",
            ["Ativa", "Bloqueada", "Suspensa", "Inativa"],
            index=["Ativa", "Bloqueada", "Suspensa", "Inativa"].index(
                empresa_atual["status_assinatura"]
                if empresa_atual["status_assinatura"] in ["Ativa", "Bloqueada", "Suspensa", "Inativa"]
                else "Ativa"
            )
        )

        motivo = st.text_area(
            "Motivo/observação do status",
            value=str(empresa_atual.get("motivo_bloqueio") or "")
        )

        if st.button("Atualizar status do assinante"):
            atualizar_status(empresa_id, novo_status, motivo)
            st.success("Status atualizado.")
            st.rerun()

    with col2:
        novo_plano = st.selectbox(
            "Plano",
            ["Teste", "Básico", "Profissional", "Premium", "Enterprise"],
            index=0
        )

        if st.button("Atualizar plano"):
            atualizar_plano(empresa_id, novo_plano)
            st.success("Plano atualizado.")
            st.rerun()

        nova_senha = st.text_input("Nova senha do assinante", type="password")

        if st.button("Resetar senha do assinante"):
            if not nova_senha:
                st.error("Informe a nova senha.")
            else:
                resetar_senha(empresa_id, nova_senha)
                st.success("Senha redefinida.")

    st.divider()

    observacao = st.text_area(
        "Observação administrativa interna",
        value=str(empresa_atual.get("observacao_admin") or "")
    )

    if st.button("Salvar observação administrativa"):
        atualizar_observacao(empresa_id, observacao)
        st.success("Observação salva.")
        st.rerun()

elif pagina == "Zona de risco":
    st.subheader("Zona de risco")

    st.warning("Use exclusão somente quando houver cadastro indevido. Para inadimplência ou bloqueio comercial, prefira status Bloqueada ou Suspensa.")

    if empresas.empty:
        st.info("Nenhum assinante cadastrado.")
        st.stop()

    empresa_opcao = st.selectbox(
        "Selecionar assinante para exclusão",
        empresas.apply(
            lambda r: f"{r['id']} | {r['nome']} | {r['cnpj_cpf']}",
            axis=1
        ).tolist()
    )

    empresa_id = int(empresa_opcao.split("|")[0].strip())

    st.error("A exclusão remove a empresa e dados operacionais relacionados no banco atual.")

    confirmacao = st.text_input(f"Digite EXCLUIR {empresa_id} para confirmar")

    if st.button("Excluir assinante definitivamente"):
        if confirmacao == f"EXCLUIR {empresa_id}":
            excluir_empresa(empresa_id)
            st.success("Assinante excluído definitivamente.")
            st.rerun()
        else:
            st.error("Confirmação inválida.")

st.caption("GOIA · Área Master da plataforma")
