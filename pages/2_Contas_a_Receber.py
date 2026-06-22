import streamlit as st
from utils.ui import aplicar_estilo_premium
from utils.premium import aplicar_premium_goia, hero
import pandas as pd
import sqlite3
from datetime import datetime, date
from utils.auth import empresa_logada, exigir_login

DB_PATH = "bd/gofinance.db"

exigir_login()
EMPRESA_ID_ATIVA = empresa_logada()

st.set_page_config(
    page_title="GOIA | Contas a Receber",
    page_icon="GOIA",
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

hero(
    "Contas a Receber",
    "Gestao dos recebimentos, clientes, documentos fiscais, baixas e rastreabilidade financeira.",
    icone="GOIA"
)


def moeda(valor):
    try:
        valor = float(valor or 0)
    except Exception:
        valor = 0.0
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def carregar_contas_receber():
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            cr.id,
            cr.empresa_id,
            cr.cliente_id,
            COALESCE(c.nome, 'Cliente não identificado') AS cliente,
            COALESCE(c.cnpj_cpf, '') AS cnpj_cpf,
            cr.documento_id,
            COALESCE(d.tipo_documento, 'Sem documento') AS documento,
            COALESCE(d.numero_nfe, '') AS numero_nfe,
            COALESCE(d.chave_acesso_nfe, '') AS chave_acesso_nfe,
            cr.descricao,
            cr.valor,
            cr.data_emissao,
            cr.data_vencimento,
            COALESCE(cr.data_baixa, '') AS data_baixa,
            COALESCE(cr.valor_baixado, 0) AS valor_baixado,
            COALESCE(cr.observacao_baixa, '') AS observacao_baixa,
            COALESCE(cr.status, 'Pendente') AS status,
            cr.criado_em
        FROM contas_receber cr
        LEFT JOIN clientes c
            ON c.id = cr.cliente_id
           AND c.empresa_id = cr.empresa_id
        LEFT JOIN documentos d
            ON d.id = cr.documento_id
           AND d.empresa_id = cr.empresa_id
        WHERE cr.empresa_id = ?
        ORDER BY
            CASE
                WHEN COALESCE(cr.status, 'Pendente') IN ('Pendente', 'Aberto') THEN 1
                WHEN COALESCE(cr.status, 'Pendente') IN ('Baixada', 'Baixado', 'Liquidado') THEN 2
                ELSE 3
            END,
            cr.data_vencimento ASC,
            cr.id DESC
    """

    df = pd.read_sql_query(query, conn, params=(EMPRESA_ID_ATIVA,))
    conn.close()
    return df


df = carregar_contas_receber()

if df.empty:
    st.warning("Nenhuma conta a receber cadastrada ainda.")
    st.stop()

df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
df["valor_baixado"] = pd.to_numeric(df["valor_baixado"], errors="coerce").fillna(0)
df["status"] = df["status"].fillna("Pendente")

df["data_vencimento_dt"] = pd.to_datetime(df["data_vencimento"], errors="coerce")
df["data_baixa_dt"] = pd.to_datetime(df["data_baixa"], errors="coerce")

hoje = pd.Timestamp(date.today())

status_baixado = ["Baixada", "Baixado", "Liquidado"]
status_aberto = ~df["status"].isin(status_baixado)

total_a_receber = df[status_aberto]["valor"].sum()
total_baixado = df[df["status"].isin(status_baixado)]["valor_baixado"].sum()
total_vencido = df[
    status_aberto &
    df["data_vencimento_dt"].notna() &
    (df["data_vencimento_dt"] < hoje)
]["valor"].sum()

qtd_pendente = len(df[status_aberto])
qtd_sem_documento = len(df[df["documento_id"].isna()])
qtd_sem_cliente = len(df[df["cliente"] == "Cliente não identificado"])

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("A Receber", moeda(total_a_receber))

with col2:
    st.metric("Recebido / Baixado", moeda(total_baixado))

with col3:
    st.metric("Vencido", moeda(total_vencido))

with col4:
    st.metric("Títulos Pendentes", qtd_pendente)

st.divider()

st.subheader("Filtros")

colf1, colf2, colf3, colf4 = st.columns(4)

with colf1:
    status_opcoes = ["Todos"] + sorted(df["status"].dropna().unique().tolist())
    filtro_status = st.selectbox("Status", status_opcoes)

with colf2:
    clientes_opcoes = ["Todos"] + sorted(df["cliente"].dropna().unique().tolist())
    filtro_cliente = st.selectbox("Cliente", clientes_opcoes)

with colf3:
    filtro_vencidos = st.checkbox("Somente vencidos")

with colf4:
    filtro_sem_documento = st.checkbox("Sem documento vinculado")

df_filtrado = df.copy()

if filtro_status != "Todos":
    df_filtrado = df_filtrado[df_filtrado["status"] == filtro_status]

if filtro_cliente != "Todos":
    df_filtrado = df_filtrado[df_filtrado["cliente"] == filtro_cliente]

if filtro_vencidos:
    df_filtrado = df_filtrado[
        (~df_filtrado["status"].isin(status_baixado)) &
        df_filtrado["data_vencimento_dt"].notna() &
        (df_filtrado["data_vencimento_dt"] < hoje)
    ]

if filtro_sem_documento:
    df_filtrado = df_filtrado[df_filtrado["documento_id"].isna()]

st.divider()

st.subheader("Títulos a Receber")

df_exibicao = df_filtrado[[
    "id",
    "cliente",
    "cnpj_cpf",
    "documento",
    "numero_nfe",
    "descricao",
    "valor",
    "data_emissao",
    "data_vencimento",
    "status",
    "data_baixa",
    "valor_baixado",
    "documento_id"
]].copy()

df_exibicao["valor"] = df_exibicao["valor"].apply(moeda)
df_exibicao["valor_baixado"] = df_exibicao["valor_baixado"].apply(moeda)

st.dataframe(
    df_exibicao,
    use_container_width=True,
    hide_index=True
)

st.divider()

st.subheader("Governança do Recebimento")

colg1, colg2, colg3 = st.columns(3)

with colg1:
    st.metric("Sem Documento", qtd_sem_documento)

with colg2:
    st.metric("Sem Cliente Identificado", qtd_sem_cliente)

with colg3:
    baixados_sem_valor = len(
        df[
            df["status"].isin(status_baixado) &
            (df["valor_baixado"] <= 0)
        ]
    )
    st.metric("Baixados sem Valor", baixados_sem_valor)

st.caption(
    "Regra GOIA: todo recebimento deve responder de onde veio, qual cliente, qual documento, se foi conciliado, baixado e arquivado."
)

st.divider()

st.subheader("Detalhamento do Recebimento")

ids = df_filtrado["id"].tolist()

if not ids:
    st.info("Nenhum título encontrado com os filtros selecionados.")
else:
    titulo_id = st.selectbox("Selecione um título para análise", ids)

    detalhe = df[df["id"] == titulo_id].iloc[0]

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        st.markdown("### Origem")
        st.write(f"**Cliente:** {detalhe['cliente']}")
        st.write(f"**CPF/CNPJ:** {detalhe['cnpj_cpf'] or 'Não informado'}")
        st.write(f"**Documento:** {detalhe['documento']}")
        st.write(f"**NF-e:** {detalhe['numero_nfe'] or 'Não vinculada'}")
        st.write(f"**Descrição:** {detalhe['descricao'] or 'Sem descrição'}")

    with col_d2:
        st.markdown("### Financeiro")
        st.write(f"**Valor:** {moeda(detalhe['valor'])}")
        st.write(f"**Vencimento:** {detalhe['data_vencimento'] or 'Não informado'}")
        st.write(f"**Status:** {detalhe['status']}")
        st.write(f"**Data da baixa:** {detalhe['data_baixa'] or 'Não baixado'}")
        st.write(f"**Valor baixado:** {moeda(detalhe['valor_baixado'])}")

    pendencias = []

    if detalhe["cliente"] == "Cliente não identificado":
        pendencias.append("Cliente não identificado.")

    if pd.isna(detalhe["documento_id"]):
        pendencias.append("Título sem documento vinculado.")

    if detalhe["status"] not in status_baixado:
        pendencias.append("Título ainda não baixado.")

    if detalhe["status"] in status_baixado and float(detalhe["valor_baixado"] or 0) <= 0:
        pendencias.append("Título baixado sem valor de baixa registrado.")

    if pendencias:
        st.warning("Pendências identificadas:")
        for p in pendencias:
            st.write(f"- {p}")
    else:
        st.success("Recebimento com informações principais consistentes.")
