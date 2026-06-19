
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
st.subheader("Visão executiva document-driven")
st.caption("Documentos, compras, vendas, contas, conciliações, retenções e processos em uma visão única.")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Receita bruta", moeda(recebimentos))

with col2:
    st.metric("Pagamentos", moeda(pagamentos))

with col3:
    st.metric("Margem operacional", moeda(saldo))

with col4:
    st.metric("Pendências abertas", pendencias)

st.divider()

st.subheader("Processo em destaque")

conn = conectar()
try:
    processo = pd.read_sql_query("""
        SELECT
            titulo,
            contraparte_nome,
            valor_total,
            valor_recebido,
            valor_retido,
            margem_bruta,
            status,
            proxima_acao
        FROM processos_documentais
        WHERE empresa_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, conn, params=(EMPRESA_ID,))
except:
    processo = pd.DataFrame()
conn.close()

if processo.empty:
    st.info("Nenhum processo documental encontrado.")
else:
    p0 = processo.iloc[0]
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Valor faturado", moeda(p0.get("valor_total", 0)))
    with c2:
        st.metric("Recebido em banco", moeda(p0.get("valor_recebido", 0)))
    with c3:
        st.metric("Retenção", moeda(p0.get("valor_retido", 0)))
    with c4:
        st.metric("Margem", moeda(p0.get("margem_bruta", 0)))

    with st.container(border=True):
        st.markdown(f"### {p0.get('titulo', 'Processo')}")
        st.write(f"**Contraparte:** {p0.get('contraparte_nome', '')}")
        st.write(f"**Status:** {p0.get('status', '')}")
        st.write(f"**Próxima ação:** {p0.get('proxima_acao', '')}")

st.divider()

st.subheader("Módulos principais")

m1, m2, m3 = st.columns(3)

with m1:
    with st.container(border=True):
        st.markdown("### 📄 Importar Documento")
        st.write("Entrada única para PDF, XML, imagens, planilhas, extratos, comprovantes e documentos financeiros.")
        st.page_link("pages/1_Importar_Documento.py", label="Acessar importação")

with m2:
    with st.container(border=True):
        st.markdown("### 🗂️ Processos Documentais")
        st.write("Agrupa documentos, evidências, pendências, compras, vendas, baixas e encerramento.")
        st.page_link("pages/7_Processos_Documentais.py", label="Acessar processos")

with m3:
    with st.container(border=True):
        st.markdown("### 🏦 Conciliação Bancária")
        st.write("Valida banco, contas a receber, contas a pagar, comprovantes e retenções.")
        st.page_link("pages/8_Conciliacao_Bancaria.py", label="Acessar conciliação")

st.divider()

st.subheader("Movimentações operacionais")

if df.empty:
    st.info("Nenhuma movimentação financeira encontrada.")
else:
    df_view = df.copy()
    df_view["data"] = df_view["data"].apply(data_br)
    df_view["valor"] = df_view["valor"].apply(moeda)
    st.dataframe(df_view, width="stretch", hide_index=True)

st.caption("GOIA Finance Platform · Documentos → Evidências → Operação → Conciliação → Encerramento")
