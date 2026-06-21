import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


DB_PATH = "bd/gofinance.db"
from utils.auth import empresa_logada, exigir_login

exigir_login()

EMPRESA_ID = empresa_logada()


st.set_page_config(
    page_title="Pendências Inteligentes",
    page_icon="⚠️",
    layout="wide"
)


st.markdown("""
<style>
[data-testid="stSidebarNav"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)


def menu_goia():
    st.sidebar.markdown("## GOIA")
    st.sidebar.page_link("app.py", label="Dashboard", icon="🏠")
    st.sidebar.page_link("pages/1_Importar_Documento.py", label="Importar Documento", icon="📄")
    st.sidebar.page_link("pages/9_Clientes.py", label="Clientes", icon="👥")
    st.sidebar.page_link("pages/10_Fornecedores.py", label="Fornecedores", icon="🏭")
    st.sidebar.page_link("pages/2_Contas_a_Receber.py", label="Contas a Receber", icon="💰")
    st.sidebar.page_link("pages/3_Contas_a_Pagar.py", label="Contas a Pagar", icon="💸")
    st.sidebar.page_link("pages/7_Processos_Documentais.py", label="Processos Documentais", icon="🗂️")
    st.sidebar.page_link("pages/8_Conciliacao_Bancaria.py", label="Conciliação Bancária", icon="🏦")

menu_goia()



st.title("⚠️ Pendências Inteligentes")
st.caption("Pendências documentais e financeiras que exigem ação operacional.")


def conectar():
    return sqlite3.connect(DB_PATH)


def carregar_pendencias():
    conn = conectar()

    query = """
        SELECT
            pp.id AS pendencia_id,
            pd.titulo AS processo,
            pd.tipo_operacao,
            pd.contraparte_nome,
            pd.valor_total,
            pp.descricao,
            pp.tipo_evidencia,
            pp.status,
            pd.proxima_acao
        FROM processo_pendencias pp
        LEFT JOIN processos_documentais pd
            ON pd.id = pp.processo_id
        WHERE pp.empresa_id = ?
        ORDER BY
            CASE pp.status
                WHEN 'Pendente' THEN 1
                WHEN 'Em análise' THEN 2
                WHEN 'Resolvida' THEN 3
                ELSE 4
            END,
            pp.id DESC
    """

    try:
        df = pd.read_sql_query(query, conn, params=(EMPRESA_ID,))
    except Exception:
        df = pd.DataFrame()

    conn.close()
    return df


def formatar_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


df = carregar_pendencias()

if df.empty:
    st.info("Nenhuma pendência documental encontrada.")
    st.stop()

total = len(df)
pendentes = len(df[df["status"] == "Pendente"])
em_analise = len(df[df["status"] == "Em análise"])
resolvidas = len(df[df["status"] == "Resolvida"])

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Total de pendências", total)

with c2:
    st.metric("Pendentes", pendentes)

with c3:
    st.metric("Em análise", em_analise)

with c4:
    st.metric("Resolvidas", resolvidas)

st.divider()

st.subheader("Pendências que exigem ação")

filtro_status = st.selectbox(
    "Filtrar por status",
    ["Todas", "Pendente", "Em análise", "Resolvida"]
)

df_view = df.copy()

if filtro_status != "Todas":
    df_view = df_view[df_view["status"] == filtro_status]

df_view["valor_total"] = df_view["valor_total"].apply(formatar_moeda)

df_view = df_view.rename(columns={
    "pendencia_id": "ID",
    "processo": "Processo",
    "tipo_operacao": "Operação",
    "contraparte_nome": "Contraparte",
    "valor_total": "Valor",
    "descricao": "Pendência",
    "tipo_evidencia": "Evidência esperada",
    "status": "Status",
    "proxima_acao": "Próxima ação"
})

st.dataframe(
    df_view,
    use_container_width=True,
    hide_index=True
)

st.divider()

st.subheader("Leitura operacional")

for _, row in df.head(5).iterrows():
    with st.container(border=True):
        st.markdown(f"### {row['descricao']}")
        st.write(f"**Processo:** {row['processo']}")
        st.write(f"**Contraparte:** {row['contraparte_nome']}")
        st.write(f"**Valor:** {formatar_moeda(row['valor_total'])}")
        st.write(f"**Evidência esperada:** {row['tipo_evidencia']}")
        st.warning(f"Próxima ação: {row['proxima_acao']}")

st.caption("GOIA Finance Platform · Pendências Inteligentes")