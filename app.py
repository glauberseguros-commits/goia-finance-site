
import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path

DB_PATH = "bd/gofinance.db"
EMPRESA_ID = 1

st.set_page_config(
    page_title="GOIA Finance Platform",
    page_icon="💰",
    layout="wide"
)


st.markdown("""
<style>
[data-testid="stSidebarNav"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)


def conectar():
    return sqlite3.connect(DB_PATH)

def moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def data_br(valor):
    if valor is None or valor == "":
        return ""
    try:
        return pd.to_datetime(valor).strftime("%d/%m/%Y")
    except:
        return valor

def carregar_movimentacoes():
    conn = conectar()

    try:
        receber = pd.read_sql_query("""
            SELECT
                data_vencimento AS data,
                'Receber' AS tipo,
                descricao,
                categoria,
                valor,
                status
            FROM contas_receber
            WHERE empresa_id = ?
        """, conn, params=(EMPRESA_ID,))
    except:
        receber = pd.DataFrame(columns=["data", "tipo", "descricao", "categoria", "valor", "status"])

    try:
        pagar = pd.read_sql_query("""
            SELECT
                data_vencimento AS data,
                'Pagar' AS tipo,
                descricao,
                categoria,
                -valor AS valor,
                status
            FROM contas_pagar
            WHERE empresa_id = ?
        """, conn, params=(EMPRESA_ID,))
    except:
        pagar = pd.DataFrame(columns=["data", "tipo", "descricao", "categoria", "valor", "status"])

    conn.close()

    df = pd.concat([receber, pagar], ignore_index=True)

    if df.empty:
        return pd.DataFrame(columns=["data", "tipo", "descricao", "categoria", "valor", "status"])

    return df

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
    except:
        total = 0

    conn.close()
    return total

def ultimo_documento():
    conn = conectar()
    conn.row_factory = sqlite3.Row

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                id,
                tipo_documento,
                direcao,
                nome_emitente,
                nome_destinatario,
                valor,
                status_processamento,
                numero_nfe,
                serie_nfe
            FROM documentos
            WHERE empresa_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (EMPRESA_ID,))
        row = cur.fetchone()
    except:
        row = None

    conn.close()
    return dict(row) if row else None

df = carregar_movimentacoes()

recebimentos = df[df["tipo"] == "Receber"]["valor"].sum() if not df.empty else 0
pagamentos = abs(df[df["tipo"] == "Pagar"]["valor"].sum()) if not df.empty else 0
saldo = recebimentos - pagamentos
pendencias = contar_pendencias()

st.sidebar.markdown("## GOIA")

st.sidebar.page_link("app.py", label="Dashboard", icon="🏠")
st.sidebar.page_link("pages/1_Importar_Documento.py", label="Importar Documento", icon="📄")
st.sidebar.page_link("pages/2_Contas_a_Receber.py", label="Contas a Receber", icon="💰")
st.sidebar.page_link("pages/3_Contas_a_Pagar.py", label="Contas a Pagar", icon="💸")
st.sidebar.page_link("pages/4_Compras.py", label="Compras", icon="🛒")
st.sidebar.page_link("pages/5_Produtos_Estoque.py", label="Produtos Estoque", icon="📦")
st.sidebar.page_link("pages/6_Vendas.py", label="Vendas", icon="🧾")
st.sidebar.page_link("pages/7_Processos_Documentais.py", label="Processos Documentais", icon="🗂️")
st.sidebar.page_link("pages/8_Conciliacao_Bancaria.py", label="Conciliação Bancária", icon="🏦")

st.title("GOIA Finance Platform")
st.subheader("Inteligência que transforma finanças")
st.caption("Automação financeira document-driven para importar documentos, estruturar compras e vendas, controlar contas a pagar e receber, acompanhar processos documentais e apoiar a conciliação bancária.")

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

m1, m2, m3 = st.columns(3)

with m1:
    with st.container(border=True):
        st.markdown("### 📄 Importar Documento")
        st.write("Entrada única para notas, comprovantes, boletos, extratos e documentos financeiros.")
        st.page_link("pages/1_Importar_Documento.py", label="Acessar importação")

with m2:
    with st.container(border=True):
        st.markdown("### 🏦 Conciliação Bancária")
        st.write("Cruzamento entre movimentos bancários, contas a pagar, contas a receber e comprovantes.")
        st.page_link("pages/8_Conciliacao_Bancaria.py", label="Acessar conciliação")

with m3:
    with st.container(border=True):
        st.markdown("### 🗂️ Processos Documentais")
        st.write("Controle de pendências, evidências e encerramento financeiro por documento.")
        st.page_link("pages/7_Processos_Documentais.py", label="Acessar processos")

st.divider()

doc = ultimo_documento()

st.subheader("Inteligência documental")

if doc:
    with st.container(border=True):
        st.markdown(f"### {doc.get('tipo_documento') or 'Documento'}")
        st.write(f"**Direção:** {doc.get('direcao') or 'A classificar'}")
        st.write(f"**Valor:** {moeda(doc.get('valor') or 0)}")
        st.write(f"**Status:** {doc.get('status_processamento') or 'Processado'}")
else:
    with st.container(border=True):
        st.markdown("### Nenhum documento processado ainda")
        st.write("Importe uma NF-e, boleto, comprovante ou extrato para iniciar o fluxo document-driven.")

st.divider()

st.subheader("Movimentações financeiras")

if df.empty:
    st.info("Nenhuma movimentação financeira encontrada. Importe o primeiro documento para iniciar.")
else:
    df_view = df.copy()
    df_view["data"] = df_view["data"].apply(data_br)
    df_view["valor"] = df_view["valor"].apply(moeda)
    st.dataframe(df_view, use_container_width=True, hide_index=True)

st.caption("GOIA Finance Platform · Dashboard nativo Streamlit")

