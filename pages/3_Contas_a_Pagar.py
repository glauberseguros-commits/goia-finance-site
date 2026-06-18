import streamlit as st
import pandas as pd
import sqlite3
from utils.financeiro import baixar_conta_pagar
from datetime import datetime
from utils.formatadores import formatar_data, formatar_moeda

DB_PATH = "bd/gofinance.db"

st.set_page_config(
    page_title="Contas a Pagar",
    page_icon="💸",
    layout="wide"
)

st.title("💸 Contas a Pagar")
st.caption("Títulos pendentes, baixados e em aberto.")

def moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def carregar_contas_pagar():
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            cp.id,
            COALESCE(f.nome, 'Fornecedor não identificado') AS fornecedor,
            COALESCE(d.tipo_documento, 'Documento') AS documento,
            d.numero_nfe,
            d.serie_nfe,
            cp.descricao,
            cp.valor,
            cp.data_emissao,
            cp.data_vencimento,
            cp.status,
            cp.criado_em
        FROM contas_pagar cp
        LEFT JOIN fornecedores f ON f.id = cp.fornecedor_id
        LEFT JOIN documentos d ON d.id = cp.documento_id
        ORDER BY cp.data_vencimento ASC, cp.id DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

df = carregar_contas_pagar()

if df.empty:
    st.warning("Nenhuma conta a pagar cadastrada ainda.")
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
    st.metric("A pagar", moeda(total_pendente))

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

df_exibicao["origem"] = df_exibicao.apply(
    lambda r: f"NF-e {r['numero_nfe']}/Série {r['serie_nfe']}" if pd.notna(r["numero_nfe"]) and str(r["numero_nfe"]).strip() else r["documento"],
    axis=1
)

df_exibicao["valor"] = df_exibicao["valor"].apply(moeda)

for col in ["data_emissao", "data_vencimento", "criado_em"]:
    if col in df_exibicao.columns:
        df_exibicao[col] = df_exibicao[col].fillna("").apply(formatar_data)

df_exibicao = df_exibicao[[
    "id",
    "fornecedor",
    "origem",
    "descricao",
    "valor",
    "data_emissao",
    "data_vencimento",
    "status",
    "dias_em_aberto"
]]

df_exibicao = df_exibicao.rename(columns={
    "id": "ID",
    "fornecedor": "Fornecedor",
    "origem": "Origem",
    "descricao": "Descrição",
    "valor": "Valor",
    "data_emissao": "Emissão",
    "data_vencimento": "Vencimento",
    "status": "Status",
    "dias_em_aberto": "Dias em aberto"
})

st.dataframe(
    df_exibicao,
    width="stretch",
    hide_index=True
)

st.divider()

st.subheader("Baixar pagamento manualmente")

ids_pendentes = df[df["status"] == "Pendente"]["id"].tolist()

if not ids_pendentes:
    st.info("Não há contas pendentes para pagar.")
else:
    conta_id = st.selectbox("Selecione o ID da conta", ids_pendentes)

    if st.button("Baixar conta a pagar"):
        try:
            baixar_conta_pagar(
                int(conta_id),
                EMPRESA_ID_ATIVA,
                observacao="Baixa manual via tela Contas a Pagar"
            )
            st.success("Conta a pagar baixada e processo documental atualizado.")
            st.rerun()
        except Exception as e:
            st.error(str(e))
