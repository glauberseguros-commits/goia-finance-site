import streamlit as st
from utils.ui import aplicar_estilo_premium
import pandas as pd
import sqlite3
from utils.formatadores import formatar_data
from utils.auth import empresa_logada, exigir_login

DB_PATH = "bd/gofinance.db"

exigir_login()
EMPRESA_ID_ATIVA = empresa_logada()

st.set_page_config(
    page_title="Compras",
    page_icon="🛒",
    layout="wide"
)

aplicar_estilo_premium()

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
    st.sidebar.page_link("pages/4_Compras.py", label="Compras", icon="🛒")
    st.sidebar.page_link("pages/6_Vendas.py", label="Vendas", icon="🧾")
    st.sidebar.page_link("pages/7_Processos_Documentais.py", label="Processos Documentais", icon="🗂️")
    st.sidebar.page_link("pages/8_Conciliacao_Bancaria.py", label="Conciliação Bancária", icon="🏦")


menu_goia()

st.title("🛒 Compras")
st.caption("Compras importadas, itens vinculados e origem fiscal.")


def moeda(valor):
    try:
        valor = float(valor or 0)
    except Exception:
        valor = 0.0

    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def carregar_compras():
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            c.id,
            c.documento_id,
            COALESCE(f.nome, 'Fornecedor não identificado') AS fornecedor,
            COALESCE(d.numero_nfe, '') AS numero_nfe,
            COALESCE(d.serie_nfe, '') AS serie_nfe,
            COALESCE(d.chave_acesso_nfe, '') AS chave_acesso_nfe,
            c.descricao,
            c.valor_total,
            c.data_compra,
            c.status,
            c.criado_em
        FROM compras c
        LEFT JOIN fornecedores f
            ON f.id = c.fornecedor_id
           AND f.empresa_id = c.empresa_id
        LEFT JOIN documentos d
            ON d.id = c.documento_id
           AND d.empresa_id = c.empresa_id
        WHERE c.empresa_id = ?
        ORDER BY c.data_compra DESC, c.id DESC
    """

    df = pd.read_sql_query(query, conn, params=(EMPRESA_ID_ATIVA,))
    conn.close()

    return df


def carregar_itens_compra(compra_id):
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            ci.id,
            COALESCE(p.descricao, ci.descricao) AS produto,
            ci.descricao,
            ci.quantidade,
            ci.valor_unitario,
            ci.valor_total
        FROM compras_itens ci
        LEFT JOIN produtos p
            ON p.id = ci.produto_id
           AND p.empresa_id = ci.empresa_id
        WHERE ci.compra_id = ?
          AND ci.empresa_id = ?
        ORDER BY ci.id
    """

    df = pd.read_sql_query(query, conn, params=(compra_id, EMPRESA_ID_ATIVA))
    conn.close()

    return df


df = carregar_compras()

if df.empty:
    st.warning("Nenhuma compra cadastrada ainda.")
    st.stop()

df["valor_total"] = pd.to_numeric(df["valor_total"], errors="coerce").fillna(0)
df["status"] = df["status"].fillna("Aberta")

total_aberto = df[df["status"] == "Aberta"]["valor_total"].sum()
total_compras = df["valor_total"].sum()
qtd_compras = len(df)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total em aberto", moeda(total_aberto))

with col2:
    st.metric("Total comprado", moeda(total_compras))

with col3:
    st.metric("Compras", qtd_compras)

st.divider()

col_f1, col_f2 = st.columns(2)

with col_f1:
    filtro_status = st.selectbox(
        "Filtrar por status",
        ["Todos"] + sorted(df["status"].dropna().unique().tolist())
    )

with col_f2:
    filtro_fornecedor = st.selectbox(
        "Filtrar por fornecedor",
        ["Todos"] + sorted(df["fornecedor"].dropna().unique().tolist())
    )

df_filtrado = df.copy()

if filtro_status != "Todos":
    df_filtrado = df_filtrado[df_filtrado["status"] == filtro_status]

if filtro_fornecedor != "Todos":
    df_filtrado = df_filtrado[df_filtrado["fornecedor"] == filtro_fornecedor]

df_exibicao = df_filtrado.copy()


def montar_origem(row):
    numero = row.get("numero_nfe")
    serie = row.get("serie_nfe")

    if str(numero or "").strip():
        if str(serie or "").strip():
            return f"NF-e {numero}/Série {serie}"
        return f"NF-e {numero}"

    return "Documento"


df_exibicao["Origem"] = df_exibicao.apply(montar_origem, axis=1)
df_exibicao["valor_total"] = df_exibicao["valor_total"].apply(moeda)

for col in ["data_compra", "criado_em"]:
    if col in df_exibicao.columns:
        df_exibicao[col] = df_exibicao[col].fillna("").apply(formatar_data)

df_exibicao = df_exibicao[[
    "id",
    "fornecedor",
    "Origem",
    "descricao",
    "valor_total",
    "data_compra",
    "status"
]]

df_exibicao = df_exibicao.rename(columns={
    "id": "ID",
    "fornecedor": "Fornecedor",
    "descricao": "Descrição",
    "valor_total": "Valor",
    "data_compra": "Data",
    "status": "Status"
})

st.dataframe(
    df_exibicao,
    width="stretch",
    hide_index=True
)

st.divider()

st.subheader("Detalhar compra")

ids = df_filtrado["id"].tolist()

if not ids:
    st.info("Nenhuma compra encontrada com os filtros selecionados.")
    st.stop()

compra_id = st.selectbox("Selecione o ID da compra", ids)

compra = df[df["id"] == compra_id].iloc[0]

col_d1, col_d2, col_d3 = st.columns(3)

with col_d1:
    st.info(f"Fornecedor: {compra['fornecedor']}")

with col_d2:
    st.info(f"Valor: {moeda(float(compra['valor_total']))}")

with col_d3:
    st.info(f"Status: {compra['status']}")

st.markdown("### Dados fiscais")

col_nf1, col_nf2 = st.columns(2)

with col_nf1:
    st.text_input("NF-e", value=str(compra["numero_nfe"] or ""), disabled=True)

with col_nf2:
    st.text_input("Série", value=str(compra["serie_nfe"] or ""), disabled=True)

st.text_input("Chave de acesso", value=str(compra["chave_acesso_nfe"] or ""), disabled=True)

st.markdown("### Itens da compra")

df_itens = carregar_itens_compra(compra_id)

if df_itens.empty:
    st.warning("Nenhum item vinculado a esta compra.")
else:
    df_itens_exibicao = df_itens.copy()

    df_itens_exibicao["valor_unitario"] = pd.to_numeric(
        df_itens_exibicao["valor_unitario"],
        errors="coerce"
    ).fillna(0).apply(moeda)

    df_itens_exibicao["valor_total"] = pd.to_numeric(
        df_itens_exibicao["valor_total"],
        errors="coerce"
    ).fillna(0).apply(moeda)

    df_itens_exibicao = df_itens_exibicao.rename(columns={
        "id": "ID",
        "produto": "Produto",
        "descricao": "Descrição",
        "quantidade": "Quantidade",
        "valor_unitario": "Valor unitário",
        "valor_total": "Valor total"
    })

    st.dataframe(
        df_itens_exibicao,
        width="stretch",
        hide_index=True
    )

st.caption("Versão 0.2 - Compras multiempresa")