import streamlit as st
import pandas as pd
import sqlite3
from utils.financeiro import baixar_conta_receber
from datetime import datetime
from utils.formatadores import formatar_data, formatar_moeda

DB_PATH = "bd/gofinance.db"

st.set_page_config(
    page_title="Contas a Receber",
    page_icon="💵",
    layout="wide"
)

st.title("💵 Contas a Receber")
st.caption("Títulos pendentes, baixados e em aberto.")

def moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def carregar_contas_receber():
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            cr.id,
            COALESCE(c.nome, 'Cliente não identificado') AS cliente,
            COALESCE(d.tipo_documento, 'Documento') AS documento,
            cr.descricao,
            cr.valor,
            cr.data_emissao,
            cr.data_vencimento,
            cr.status,
            cr.criado_em
        FROM contas_receber cr
        LEFT JOIN clientes c ON c.id = cr.cliente_id
        LEFT JOIN documentos d ON d.id = cr.documento_id
        ORDER BY cr.data_emissao DESC, cr.id DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

df = carregar_contas_receber()

if df.empty:
    st.warning("Nenhuma conta a receber cadastrada ainda.")
    st.stop()

df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)

hoje = datetime.today().date()

def calcular_dias(row):
    data_ref = row["data_vencimento"] or row["data_emissao"]
    if not data_ref:
        return 0
    try:
        data = datetime.strptime(data_ref, "%Y-%m-%d").date()
        return (hoje - data).days
    except:
        return 0

df["dias_em_aberto"] = df.apply(calcular_dias, axis=1)

total_pendente = df[df["status"] == "Pendente"]["valor"].sum()
total_baixado = df[df["status"] == "Baixada"]["valor"].sum()
qtd_pendente = len(df[df["status"] == "Pendente"])

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("A receber", moeda(total_pendente))

with col2:
    st.metric("Baixado", moeda(total_baixado))

with col3:
    st.metric("Pendentes", qtd_pendente)

st.divider()

col_f1, col_f2 = st.columns(2)

with col_f1:
    filtro_status = st.selectbox(
        "Filtrar por status",
        ["Todos"] + sorted(df["status"].dropna().unique().tolist())
    )

with col_f2:
    filtro_cliente = st.selectbox(
        "Filtrar por cliente",
        ["Todos"] + sorted(df["cliente"].dropna().unique().tolist())
    )

df_filtrado = df.copy()

if filtro_status != "Todos":
    df_filtrado = df_filtrado[df_filtrado["status"] == filtro_status]

if filtro_cliente != "Todos":
    df_filtrado = df_filtrado[df_filtrado["cliente"] == filtro_cliente]

df_exibicao = df_filtrado.copy()

df_exibicao["valor"] = df_exibicao["valor"].apply(moeda)

for col in ["data_emissao", "data_vencimento", "criado_em"]:
    if col in df_exibicao.columns:
        df_exibicao[col] = df_exibicao[col].fillna("").apply(formatar_data)

df_exibicao = df_exibicao.rename(columns={
    "id": "ID",
    "cliente": "Cliente",
    "documento": "Documento",
    "descricao": "Descrição",
    "valor": "Valor",
    "data_emissao": "Emissão",
    "data_vencimento": "Vencimento",
    "status": "Status",
    "dias_em_aberto": "Dias em aberto",
    "criado_em": "Criado em"
})

st.dataframe(
    df_exibicao,
    width="stretch",
    hide_index=True
)

st.divider()

st.subheader("Baixar recebimento manualmente")

ids_pendentes = df[df["status"] == "Pendente"]["id"].tolist()

if not ids_pendentes:
    st.info("Não há contas pendentes para baixar.")
else:
    conta_id = st.selectbox("Selecione o ID da conta", ids_pendentes)

    if st.button("Baixar conta a receber"):
        try:
            baixar_conta_receber(
                int(conta_id),
                EMPRESA_ID_ATIVA,
                observacao="Baixa manual via tela Contas a Receber"
            )
            st.success("Conta a receber baixada e processo documental atualizado.")
            st.rerun()
        except Exception as e:
            st.error(str(e))
