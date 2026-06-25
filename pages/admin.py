cd C:\Users\glaub\go-finance-ai

$admin = @'
import os
import hashlib
from datetime import datetime

import pandas as pd
import streamlit as st

from utils.db import conectar_banco, caminho_banco
from utils.schema import inicializar_schema_goia


st.set_page_config(
    page_title="Admin GOIA",
    page_icon="🛡️",
    layout="wide"
)


def conectar():
    return conectar_banco()


def hash_senha(senha):
    return hashlib.sha256(str(senha).encode("utf-8")).hexdigest()


def texto(v):
    if v is None:
        return ""
    if pd.isna(v):
        return ""
    return str(v).strip()


def moeda(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def data_br(v):
    v = texto(v)
    if not v:
        return ""
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(v[:19], fmt).strftime("%d/%m/%Y")
        except Exception:
            pass
    return v


def formatar_cnpj(v):
    n = "".join(filter(str.isdigit, texto(v)))
    if len(n) == 14:
        return f"{n[:2]}.{n[2:5]}.{n[5:8]}/{n[8:12]}-{n[12:]}"
    return texto(v)


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

        section[data-testid="stSidebar"] > div:first-child > div:first-child {
            display: none !important;
        }

        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        [data-testid="stSidebar"] * {
            color: #f8fafc !important;
            opacity: 1 !important;
            font-weight: 700 !important;
        }

        .block-container {
            max-width: 1280px !important;
            padding-top: 2.5rem !important;
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
            padding: 38px 42px;
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
            font-size: 42px;
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

        .goia-card {
            background: rgba(255,255,255,.97);
            border: 1px solid rgba(148,163,184,.35);
            border-radius: 24px;
            padding: 24px;
            box-shadow: 0 18px 42px rgba(15,23,42,.10);
            margin-bottom: 18px;
        }

        .goia-chip {
            display:inline-flex;
            align-items:center;
            gap:8px;
            padding:7px 12px;
            border-radius:999px;
            background:#eef2ff;
            color:#312e81;
            font-weight:900;
            font-size:12px;
            letter-spacing:.04em;
            text-transform:uppercase;
        }

        .goia-danger {
            background:#fff1f2;
            border:1px solid #fecdd3;
            color:#991b1b;
            border-radius:18px;
            padding:18px;
            font-weight:700;
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

        [data-testid="stTextInput"] input:disabled,
        textarea:disabled {
            background:#f8fafc !important;
            color:#0f172a !important;
            -webkit-text-fill-color:#0f172a !important;
            opacity:1 !important;
            font-weight:800 !important;
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
            font-size: 40px !important;
            font-weight: 950 !important;
        }

        [data-testid="stAlert"] {
            border-radius: 16px !important;
            border: 1px solid rgba(99,102,241,.28) !important;
        }
    </style>
    """, unsafe_allow_html=True)


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
            Painel Master para gestão de assinantes, planos, bloqueios, auditoria e operação.
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
            st.error("Senha master inválida.")

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
            senha_hash,
            situacao_cadastral,
            data_abertura,
            porte,
            natureza_juridica,
            capital_social,
            cnae_principal,
            cnaes_secundarios,
            cep,
            logradouro,
            numero,
            complemento,
            bairro,
            municipio,
            uf,
            qsa,
            plano,
            status_assinatura,
            periodo_assinatura,
            data_inicio_assinatura,
            data_fim_assinatura,
            motivo_bloqueio,
            observacao_admin,
            criado_em,
            atualizado_em
        FROM empresas
        ORDER BY id DESC
    """, conn)
    conn.close()
    return df


def carregar_empresa(empresa_id):
    conn = conectar()
    conn.row_factory = None
    df = pd.read_sql_query("""
        SELECT *
        FROM empresas
        WHERE id = ?
        LIMIT 1
    """, conn, params=(empresa_id,))
    conn.close()

    if df.empty:
        return None

    return df.iloc[0].to_dict()


def contar_tabela(tabela, empresa_id=None):
    conn = conectar()
    cur = conn.cursor()

    try:
        if empresa_id is None:
            cur.execute(f"SELECT COUNT(*) FROM {tabela}")
        else:
            cur.execute(f"SELECT COUNT(*) FROM {tabela} WHERE empresa_id = ?", (empresa_id,))
        total = cur.fetchone()[0] or 0
    except Exception:
        total = 0

    conn.close()
    return total


def soma_tabela(tabela, coluna, empresa_id=None):
    conn = conectar()
    cur = conn.cursor()

    try:
        if empresa_id is None:
            cur.execute(f"SELECT COALESCE(SUM({coluna}),0) FROM {tabela}")
        else:
            cur.execute(f"SELECT COALESCE(SUM({coluna}),0) FROM {tabela} WHERE empresa_id = ?", (empresa_id,))
        total = cur.fetchone()[0] or 0
    except Exception:
        total = 0

    conn.close()
    return total


def atualizar_admin_empresa(empresa_id, plano, status, periodo, data_fim, motivo, observacao):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        UPDATE empresas
        SET plano = ?,
            status_assinatura = ?,
            periodo_assinatura = ?,
            data_fim_assinatura = ?,
            motivo_bloqueio = ?,
            observacao_admin = ?,
            atualizado_em = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (plano, status, periodo, data_fim, motivo, observacao, empresa_id))
    conn.commit()
    conn.close()


def atualizar_status_rapido(empresa_id, status, motivo=""):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        UPDATE empresas
        SET status_assinatura = ?,
            motivo_bloqueio = ?,
            atualizado_em = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (status, motivo, empresa_id))
    conn.commit()
    conn.close()


def resetar_senha(empresa_id, nova_senha):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        UPDATE empresas
        SET senha_hash = ?,
            atualizado_em = CURRENT_TIMESTAMP
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


def campo_info(label, valor, key, area=False, height=90):
    if area:
        st.text_area(label, value=texto(valor), key=key, disabled=True, height=height)
    else:
        st.text_input(label, value=texto(valor), key=key, disabled=True)


def badge_status(status):
    status = texto(status) or "Sem status"

    if status in ["Ativa", "VIP"]:
        return f"🟢 {status}"

    if status in ["Teste"]:
        return f"🟡 {status}"

    if status in ["Suspensa", "Bloqueada", "Inativa"]:
        return f"🔴 {status}"

    return f"⚪ {status}"


def render_hero():
    st.markdown("""
    <div class="admin-hero">
        <small>GOIA Finance Platform</small>
        <h1>GOIA Control Center</h1>
        <p>Centro de controle da plataforma. Gestão de assinantes, planos, bloqueios, operação, evidências e auditoria.</p>
    </div>
    """, unsafe_allow_html=True)


def dashboard_master(empresas):
    total = len(empresas)
    ativos = len(empresas[empresas["status_assinatura"].fillna("") == "Ativa"]) if not empresas.empty else 0
    testes = len(empresas[empresas["status_assinatura"].fillna("") == "Teste"]) if not empresas.empty else 0
    suspensos = len(empresas[empresas["status_assinatura"].fillna("") == "Suspensa"]) if not empresas.empty else 0
    bloqueados = len(empresas[empresas["status_assinatura"].fillna("") == "Bloqueada"]) if not empresas.empty else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Assinantes", total)
    c2.metric("Ativos", ativos)
    c3.metric("Em teste", testes)
    c4.metric("Suspensos", suspensos)
    c5.metric("Bloqueados", bloqueados)

    st.divider()

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Documentos", contar_tabela("documentos"))
    d2.metric("Clientes", contar_tabela("clientes"))
    d3.metric("Fornecedores", contar_tabela("fornecedores"))
    d4.metric("Processos", contar_tabela("processos_documentais"))

    st.caption(f"Banco em uso: {caminho_banco()}")

    st.subheader("Últimos assinantes")

    if empresas.empty:
        st.info("Nenhum assinante cadastrado.")
        return

    cols = [
        "id",
        "nome",
        "nome_fantasia",
        "cnpj_cpf",
        "email",
        "telefone",
        "plano",
        "status_assinatura",
        "criado_em",
    ]

    df = empresas[[c for c in cols if c in empresas.columns]].copy()
    df["cnpj_cpf"] = df["cnpj_cpf"].apply(formatar_cnpj)
    df["criado_em"] = df["criado_em"].apply(data_br)

    st.dataframe(df.head(15), use_container_width=True, hide_index=True)


def selecionar_empresa(empresas):
    if empresas.empty:
        st.info("Nenhum assinante cadastrado.")
        return None

    busca = st.text_input("Buscar assinante por nome, CNPJ, e-mail, telefone ou status")

    df = empresas.copy()

    if busca.strip():
        termo = busca.strip().lower()
        df = df[
            df.astype(str).apply(
                lambda linha: linha.str.lower().str.contains(termo, na=False).any(),
                axis=1
            )
        ]

    if df.empty:
        st.warning("Nenhum assinante encontrado.")
        return None

    opcoes = df.apply(
        lambda r: f"{r['id']} | {texto(r.get('nome'))} | {formatar_cnpj(r.get('cnpj_cpf'))} | {texto(r.get('status_assinatura'))}",
        axis=1
    ).tolist()

    selecionado = st.selectbox("Selecionar assinante", opcoes)
    empresa_id = int(selecionado.split("|")[0].strip())

    return carregar_empresa(empresa_id)


def ficha_dados_oficiais(e):
    st.markdown("### Dados oficiais da empresa")

    c1, c2 = st.columns(2)
    with c1:
        campo_info("Razão Social", e.get("nome"), "view_nome")
        campo_info("Nome Fantasia", e.get("nome_fantasia"), "view_nome_fantasia")
        campo_info("CNPJ", formatar_cnpj(e.get("cnpj_cpf")), "view_cnpj")
        campo_info("Situação Cadastral", e.get("situacao_cadastral"), "view_situacao")
        campo_info("Data de Abertura", data_br(e.get("data_abertura")), "view_abertura")

    with c2:
        campo_info("Porte", e.get("porte"), "view_porte")
        campo_info("Natureza Jurídica", e.get("natureza_juridica"), "view_natureza")
        campo_info("Capital Social", moeda(e.get("capital_social")), "view_capital")
        campo_info("CNAE Principal", e.get("cnae_principal"), "view_cnae")

    campo_info("CNAEs Secundários", e.get("cnaes_secundarios"), "view_cnaes_sec", area=True, height=120)

    st.markdown("### Endereço oficial")

    e1, e2, e3 = st.columns([1, 2, 1])
    with e1:
        campo_info("CEP", e.get("cep"), "view_cep")
    with e2:
        campo_info("Logradouro", e.get("logradouro"), "view_logradouro")
    with e3:
        campo_info("Número", e.get("numero"), "view_numero")

    e4, e5, e6, e7 = st.columns([2, 2, 2, 1])
    with e4:
        campo_info("Complemento", e.get("complemento"), "view_complemento")
    with e5:
        campo_info("Bairro", e.get("bairro"), "view_bairro")
    with e6:
        campo_info("Município", e.get("municipio"), "view_municipio")
    with e7:
        campo_info("UF", e.get("uf"), "view_uf")

    campo_info("Sócios / QSA", e.get("qsa"), "view_qsa", area=True, height=140)


def ficha_contato_acesso(e):
    st.markdown("### Contato e acesso")

    c1, c2, c3 = st.columns(3)
    with c1:
        campo_info("E-mail", e.get("email"), "view_email")
    with c2:
        campo_info("Telefone", e.get("telefone"), "view_telefone")
    with c3:
        senha_status = "Configurada" if texto(e.get("senha_hash")) else "Não configurada"
        campo_info("Senha", senha_status, "view_senha_status")

    st.divider()

    st.markdown("### Reset de senha")

    nova_senha = st.text_input("Nova senha do assinante", type="password", key=f"reset_{e['id']}")

    if st.button("Resetar senha", use_container_width=True, key=f"btn_reset_{e['id']}"):
        if not nova_senha:
            st.error("Informe a nova senha.")
        else:
            resetar_senha(e["id"], nova_senha)
            st.success("Senha redefinida.")
            st.rerun()


def ficha_operacao(e):
    st.markdown("### Plano, assinatura e status")

    planos = ["Teste", "7 Dias Grátis", "Mensal", "Trimestral", "Semestral", "Anual", "VIP", "Indeterminado"]
    status_lista = ["Teste", "Ativa", "VIP", "Suspensa", "Bloqueada", "Inativa"]

    plano_atual = texto(e.get("plano")) or "Teste"
    status_atual = texto(e.get("status_assinatura")) or "Ativa"

    if plano_atual not in planos:
        planos.insert(0, plano_atual)

    if status_atual not in status_lista:
        status_lista.insert(0, status_atual)

    c1, c2, c3 = st.columns(3)

    with c1:
        plano = st.selectbox("Plano", planos, index=planos.index(plano_atual), key=f"plano_{e['id']}")
    with c2:
        status = st.selectbox("Status", status_lista, index=status_lista.index(status_atual), key=f"status_{e['id']}")
    with c3:
        periodo = st.text_input("Período", value=texto(e.get("periodo_assinatura")), key=f"periodo_{e['id']}")

    c4, c5 = st.columns(2)
    with c4:
        campo_info("Início da assinatura", data_br(e.get("data_inicio_assinatura")), f"inicio_{e['id']}")
    with c5:
        data_fim = st.text_input("Fim da assinatura", value=data_br(e.get("data_fim_assinatura")), key=f"fim_{e['id']}")

    motivo = st.text_area("Motivo de bloqueio/suspensão", value=texto(e.get("motivo_bloqueio")), key=f"motivo_{e['id']}")
    observacao = st.text_area("Observação administrativa", value=texto(e.get("observacao_admin")), key=f"obs_{e['id']}")

    if st.button("Salvar plano e status", use_container_width=True, key=f"salvar_admin_{e['id']}"):
        atualizar_admin_empresa(e["id"], plano, status, periodo, data_fim, motivo, observacao)
        st.success("Assinante atualizado.")
        st.rerun()

    st.divider()

    st.markdown("### Ações rápidas")

    a1, a2, a3, a4 = st.columns(4)

    with a1:
        if st.button("Ativar", use_container_width=True, key=f"ativar_{e['id']}"):
            atualizar_status_rapido(e["id"], "Ativa", "")
            st.success("Assinante ativado.")
            st.rerun()

    with a2:
        if st.button("Suspender", use_container_width=True, key=f"suspender_{e['id']}"):
            atualizar_status_rapido(e["id"], "Suspensa", "Suspenso pelo Admin GOIA")
            st.warning("Assinante suspenso.")
            st.rerun()

    with a3:
        if st.button("Bloquear", use_container_width=True, key=f"bloquear_{e['id']}"):
            atualizar_status_rapido(e["id"], "Bloqueada", "Bloqueado pelo Admin GOIA")
            st.warning("Assinante bloqueado.")
            st.rerun()

    with a4:
        if st.button("VIP", use_container_width=True, key=f"vip_{e['id']}"):
            atualizar_status_rapido(e["id"], "VIP", "")
            st.success("Assinante definido como VIP.")
            st.rerun()


def ficha_uso(e):
    empresa_id = e["id"]

    st.markdown("### Uso da plataforma")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Documentos", contar_tabela("documentos", empresa_id))
    c2.metric("Clientes", contar_tabela("clientes", empresa_id))
    c3.metric("Fornecedores", contar_tabela("fornecedores", empresa_id))
    c4.metric("Processos", contar_tabela("processos_documentais", empresa_id))

    c5, c6, c7 = st.columns(3)
    c5.metric("Contas a receber", contar_tabela("contas_receber", empresa_id))
    c6.metric("Contas a pagar", contar_tabela("contas_pagar", empresa_id))
    c7.metric("Movimentos bancários", contar_tabela("movimentos_bancarios", empresa_id))

    st.divider()

    r1, r2 = st.columns(2)
    r1.metric("Total a receber", moeda(soma_tabela("contas_receber", "valor", empresa_id)))
    r2.metric("Total a pagar", moeda(soma_tabela("contas_pagar", "valor", empresa_id)))


def ficha_exclusao(e):
    st.markdown("### Zona de risco")

    st.markdown("""
    <div class="goia-danger">
        A exclusão remove a empresa da tabela empresas. Para operação normal, prefira Suspensa ou Bloqueada.
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    confirmacao = st.text_input(
        f"Para excluir definitivamente, digite EXCLUIR {e['id']}",
        key=f"confirm_excluir_{e['id']}"
    )

    if st.button("Excluir definitivamente este assinante", use_container_width=True, key=f"excluir_{e['id']}"):
        if confirmacao == f"EXCLUIR {e['id']}":
            excluir_empresa(e["id"])
            st.success("Assinante excluído.")
            st.rerun()
        else:
            st.error("Confirmação inválida.")


def pagina_assinantes(empresas):
    st.subheader("Gestão de assinantes")

    empresa = selecionar_empresa(empresas)

    if not empresa:
        return

    st.markdown(f"""
    <div class="goia-card">
        <span class="goia-chip">{badge_status(empresa.get("status_assinatura"))}</span>
        <h2 style="margin:16px 0 4px 0;color:#0f172a;">{texto(empresa.get("nome"))}</h2>
        <p style="margin:0;color:#475569;font-weight:700;">
            {formatar_cnpj(empresa.get("cnpj_cpf"))} · {texto(empresa.get("email"))} · {texto(empresa.get("telefone"))}
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Dados oficiais",
        "Contato e acesso",
        "Plano e operação",
        "Uso da plataforma",
        "Zona de risco",
    ])

    with tab1:
        ficha_dados_oficiais(empresa)

    with tab2:
        ficha_contato_acesso(empresa)

    with tab3:
        ficha_operacao(empresa)

    with tab4:
        ficha_uso(empresa)

    with tab5:
        ficha_exclusao(empresa)


def pagina_financeiro(empresas):
    st.subheader("Financeiro da plataforma")

    st.info("Módulo preparado para MRR, ARR, planos, faturas, pagamentos, inadimplência e Mercado Pago.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Assinantes pagantes", len(empresas[empresas["plano"].fillna("").isin(["Mensal", "Trimestral", "Semestral", "Anual"])]))
    c2.metric("VIP", len(empresas[empresas["plano"].fillna("") == "VIP"]))
    c3.metric("Em teste", len(empresas[empresas["status_assinatura"].fillna("") == "Teste"]))


def pagina_auditoria(empresas):
    st.subheader("Auditoria e operação")

    st.info("Módulo preparado para logs de login, alterações administrativas, evidências, documentos enviados e trilha de auditoria.")

    if empresas.empty:
        st.info("Nenhum assinante cadastrado.")
        return

    cols = ["id", "nome", "cnpj_cpf", "status_assinatura", "criado_em", "atualizado_em"]
    df = empresas[[c for c in cols if c in empresas.columns]].copy()
    if "cnpj_cpf" in df.columns:
        df["cnpj_cpf"] = df["cnpj_cpf"].apply(formatar_cnpj)
    if "criado_em" in df.columns:
        df["criado_em"] = df["criado_em"].apply(data_br)
    if "atualizado_em" in df.columns:
        df["atualizado_em"] = df["atualizado_em"].apply(data_br)

    st.dataframe(df, use_container_width=True, hide_index=True)


aplicar_estilo_admin()
inicializar_schema_goia()
autenticar_master()

st.sidebar.markdown("## Admin GOIA")
st.sidebar.caption("Control Center")

pagina = st.sidebar.radio(
    "Menu",
    ["Dashboard Master", "Assinantes", "Financeiro", "Auditoria"],
    label_visibility="collapsed"
)

if st.sidebar.button("Sair do Admin"):
    st.session_state.pop("goia_admin_logado", None)
    st.rerun()

empresas = carregar_empresas()

render_hero()

if pagina == "Dashboard Master":
    dashboard_master(empresas)

elif pagina == "Assinantes":
    pagina_assinantes(empresas)

elif pagina == "Financeiro":
    pagina_financeiro(empresas)

elif pagina == "Auditoria":
    pagina_auditoria(empresas)

st.caption("GOIA · Área Master da plataforma")
'@

$admin | Set-Content .\pages\admin.py -Encoding UTF8

python -m py_compile .\pages\admin.py

git status --short
git add .\pages\admin.py
git commit -m "Reestrutura Admin GOIA Control Center"
git push