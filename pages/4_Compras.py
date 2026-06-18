import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from utils.formatadores import formatar_data, formatar_moeda

DB_PATH = "bd/gofinance.db"
EMPRESA_ID_ATIVA = 1

st.set_page_config(
    page_title="Compras",
    page_icon="🛒",
    layout="wide"
)

st.title("🛒 Compras")
st.caption("Compras importadas, itens vinculados e origem fiscal.")

def moeda(valor):
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
        LEFT JOIN fornecedores f ON f.id = c.fornecedor_id
        LEFT JOIN documentos d ON d.id = c.documento_id
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
        LEFT JOIN produtos p ON p.id = ci.produto_id
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

df_exibicao["Origem"] = df_exibicao.apply(
    lambda r: f"NF-e {r['numero_nfe']}/Série {r['serie_nfe']}" if str(r["numero_nfe"]).strip() else "Documento",
    axis=1
)

df_exibicao["valor_total"] = df_exibicao["valor_total"].apply(moeda)

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
    st.text_input("NF-e", value=compra["numero_nfe"], disabled=True)

with col_nf2:
    st.text_input("Série", value=compra["serie_nfe"], disabled=True)

st.text_input("Chave de acesso", value=compra["chave_acesso_nfe"], disabled=True)

st.markdown("### Itens da compra")

df_itens = carregar_itens_compra(compra_id)

if df_itens.empty:
    st.warning("Nenhum item vinculado a esta compra.")
else:
    df_itens_exibicao = df_itens.copy()
    df_itens_exibicao["valor_unitario"] = df_itens_exibicao["valor_unitario"].apply(moeda)
    df_itens_exibicao["valor_total"] = df_itens_exibicao["valor_total"].apply(moeda)

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

st.caption("Versão 0.1 - Compras")
