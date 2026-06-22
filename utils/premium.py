
import streamlit as st

def aplicar_premium_goia():
    st.markdown("""
    <style>
    :root {
        --goia-bg: #f6f7fb;
        --goia-card: rgba(255,255,255,.86);
        --goia-border: rgba(15,23,42,.08);
        --goia-text: #111827;
        --goia-muted: #64748b;
        --goia-accent: #ef4444;
        --goia-accent-2: #2563eb;
        --goia-success: #16a34a;
        --goia-shadow: 0 18px 45px rgba(15,23,42,.08);
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(37,99,235,.08), transparent 28%),
            linear-gradient(180deg, #ffffff 0%, var(--goia-bg) 100%);
        color: var(--goia-text);
    }

    section[data-testid="stSidebar"] {
        background: rgba(248,250,252,.92);
        border-right: 1px solid var(--goia-border);
    }

    section[data-testid="stSidebar"] * {
        font-size: 14px;
    }

    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    .block-container {
        padding-top: 48px;
        padding-bottom: 56px;
        max-width: 1500px;
    }

    h1 {
        font-size: 34px !important;
        letter-spacing: -.04em;
        font-weight: 900 !important;
        color: #111827 !important;
        margin-bottom: 4px !important;
    }

    h2, h3 {
        letter-spacing: -.03em;
        font-weight: 850 !important;
        color: #111827 !important;
    }

    div[data-testid="stMetric"] {
        background: var(--goia-card);
        border: 1px solid var(--goia-border);
        padding: 18px 20px;
        border-radius: 18px;
        box-shadow: var(--goia-shadow);
    }

    div[data-testid="stMetricLabel"] p {
        color: var(--goia-muted) !important;
        font-weight: 700 !important;
        font-size: 13px !important;
    }

    div[data-testid="stMetricValue"] {
        color: #111827 !important;
        font-weight: 850 !important;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 18px;
        overflow: hidden;
        border: 1px solid var(--goia-border);
        box-shadow: var(--goia-shadow);
    }

    div[data-testid="stAlert"] {
        border-radius: 16px;
        border: 1px solid rgba(15,23,42,.08);
    }

    .stButton > button {
        border-radius: 12px !important;
        font-weight: 800 !important;
        border: 0 !important;
        background: linear-gradient(135deg, #ef4444, #f97316) !important;
        color: white !important;
        box-shadow: 0 12px 28px rgba(239,68,68,.22);
    }

    .stDownloadButton > button {
        border-radius: 12px !important;
        font-weight: 800 !important;
    }

    .goia-hero {
        background: linear-gradient(135deg, #0f172a 0%, #111827 45%, #1e3a8a 100%);
        color: white;
        padding: 30px 34px;
        border-radius: 26px;
        box-shadow: 0 24px 65px rgba(15,23,42,.18);
        margin-bottom: 24px;
        border: 1px solid rgba(255,255,255,.12);
    }

    .goia-hero .kicker {
        font-size: 12px;
        letter-spacing: .18em;
        text-transform: uppercase;
        color: #93c5fd;
        font-weight: 900;
        margin-bottom: 10px;
    }

    .goia-hero .title {
        font-size: 34px;
        line-height: 1.1;
        font-weight: 950;
        letter-spacing: -.04em;
        margin-bottom: 8px;
    }

    .goia-hero .subtitle {
        color: #cbd5e1;
        font-size: 15px;
        max-width: 980px;
    }

    .goia-section {
        background: rgba(255,255,255,.72);
        border: 1px solid var(--goia-border);
        border-radius: 22px;
        padding: 22px;
        box-shadow: var(--goia-shadow);
        margin-top: 18px;
    }

    .goia-muted {
        color: var(--goia-muted);
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)


def hero(titulo, subtitulo="", kicker="GOIA FINANCE PLATFORM", icone="💰"):
    st.markdown(f"""
    <div class="goia-hero">
        <div class="kicker">{kicker}</div>
        <div class="title">{icone} {titulo}</div>
        <div class="subtitle">{subtitulo}</div>
    </div>
    """, unsafe_allow_html=True)


def menu_principal():
    st.sidebar.markdown("## GOIA")
    if st.session_state.get("empresa_nome"):
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
    st.sidebar.page_link("pages/8_Movimentos_Bancarios.py", label="Movimentos Bancários", icon="🏦")
    st.sidebar.page_link("pages/8_Conciliacao_Bancaria.py", label="Conciliação Bancária", icon="⚖️")
