import sqlite3

import pandas as pd
import streamlit as st
from utils.auth import empresa_logada, exigir_login
from utils.ui import aplicar_estilo_premium
from utils.premium import aplicar_premium_goia, hero

DB_PATH = "bd/gofinance.db"

exigir_login()
EMPRESA_ID_ATIVA = empresa_logada()

st.set_page_config(
    page_title="Clientes",
    page_icon="👥",
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
    st.sidebar.page_link("pages/4_Compras.py", label="Compras", icon="🛒")
    st.sidebar.page_link("pages/5_Produtos_Estoque.py", label="Produtos / Estoque", icon="📦")
    st.sidebar.page_link("pages/6_Vendas.py", label="Vendas", icon="🧾")
    st.sidebar.page_link("pages/7_Processos_Documentais.py", label="Processos Documentais", icon="🗂️")
    st.sidebar.page_link("pages/8_Conciliacao_Bancaria.py", label="Conciliação Bancária", icon="🏦")


menu_goia()

hero(
    "Clientes",
    "Clientes identificados automaticamente a partir dos documentos importados e vinculados aos processos financeiros.",
    icone="GOIA"
)


def conectar():
    return sqlite3.connect(DB_PATH)


def moeda(valor):
    try:
        return f"R$ {float(valor or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def data_br(valor):
    if not valor:
        return ""
    try:
        return pd.to_datetime(valor).strftime("%d/%m/%Y")
    except Exception:
        return str(valor)


def carregar_clientes():
    conn = conectar()

    query = """
        SELECT
            id,
            nome,
            cnpj_cpf,
            email,
            telefone,
            cidade,
            uf,
            status,
            origem_cadastro
        FROM clientes
        WHERE empresa_id = ?
        ORDER BY nome
    """

    df = pd.read_sql_query(query, conn, params=(EMPRESA_ID_ATIVA,))
    conn.close()
    return df


def carregar_notas_cliente(cliente_id):
    conn = conectar()

    query = """
        SELECT
            d.numero_nfe,
            d.serie_nfe,
            d.data_emissao,
            d.valor,
            d.status_processamento
        FROM documentos d
        INNER JOIN clientes c
            ON c.empresa_id = d.empresa_id
           AND c.id = ?
        WHERE d.empresa_id = ?
          AND d.direcao = 'Nota Fiscal de Venda'
          AND (
                IFNULL(d.cnpj_destinatario, '') = IFNULL(c.cnpj_cpf, '')
                OR IFNULL(d.nome_destinatario, '') = IFNULL(c.nome, '')
          )
        ORDER BY d.data_emissao DESC
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(cliente_id, EMPRESA_ID_ATIVA)
    )

    conn.close()
    return df


def carregar_receber_cliente(cliente_id):
    conn = conectar()

    query = """
        SELECT
            descricao,
            valor,
            valor_baixado,
            data_vencimento,
            data_baixa,
            status
        FROM contas_receber
        WHERE empresa_id = ?
          AND cliente_id = ?
        ORDER BY data_vencimento DESC
    """

    df = pd.read_sql_query(query, conn, params=(EMPRESA_ID_ATIVA, cliente_id))
    conn.close()
    return df


clientes = carregar_clientes()

st.subheader("Clientes cadastrados")

busca = st.text_input("Buscar cliente por nome ou CPF/CNPJ")

if busca and not clientes.empty:
    clientes = clientes[
        clientes["nome"].fillna("").str.contains(busca, case=False, na=False)
        | clientes["cnpj_cpf"].fillna("").str.contains(busca, case=False, na=False)
    ]

if clientes.empty:
    st.info("Nenhum cliente cadastrado. Importe documentos financeiros para o sistema classificar clientes automaticamente.")
    st.stop()

clientes_exibicao = clientes.copy()

clientes_exibicao = clientes_exibicao.rename(columns={
    "nome": "Nome",
    "cnpj_cpf": "CPF/CNPJ",
    "email": "E-mail",
    "telefone": "Telefone",
    "cidade": "Cidade",
    "uf": "UF",
    "status": "Status",
    "origem_cadastro": "Origem"
})

st.dataframe(
    clientes_exibicao.drop(columns=["id"]),
    width="stretch",
    hide_index=True
)

st.divider()
st.subheader("Histórico financeiro do cliente")

clientes["nome_exibicao"] = clientes.apply(
    lambda r: (
        f"{r['nome']} | {r['cnpj_cpf']}"
        if pd.notna(r["cnpj_cpf"]) and str(r["cnpj_cpf"]).strip()
        else str(r["nome"])
    ),
    axis=1
)

cliente_opcao = st.selectbox(
    "Selecionar cliente",
    clientes["nome_exibicao"].tolist()
)

cliente_id = int(clientes.loc[clientes["nome_exibicao"] == cliente_opcao, "id"].iloc[0])

notas = carregar_notas_cliente(cliente_id)
receber = carregar_receber_cliente(cliente_id)

st.markdown("### Notas fiscais emitidas")

if notas.empty:
    st.info("Nenhuma NF-e de venda encontrada para este cliente.")
else:
    notas_exibicao = notas.copy()
    notas_exibicao["data_emissao"] = notas_exibicao["data_emissao"].apply(data_br)
    notas_exibicao["valor"] = notas_exibicao["valor"].apply(moeda)

    notas_exibicao = notas_exibicao.rename(columns={
        "numero_nfe": "NF-e",
        "serie_nfe": "Série",
        "data_emissao": "Emissão",
        "valor": "Valor",
        "status_processamento": "Status"
    })

    st.dataframe(
        notas_exibicao,
        width="stretch",
        hide_index=True
    )

st.markdown("### Contas a receber")

if receber.empty:
    st.info("Nenhuma conta a receber encontrada para este cliente.")
else:
    receber_exibicao = receber.copy()

    receber_exibicao["data_vencimento"] = receber_exibicao["data_vencimento"].apply(data_br)
    receber_exibicao["data_baixa"] = receber_exibicao["data_baixa"].apply(data_br)
    receber_exibicao["valor"] = receber_exibicao["valor"].apply(moeda)
    receber_exibicao["valor_baixado"] = receber_exibicao["valor_baixado"].apply(moeda)

    receber_exibicao = receber_exibicao.rename(columns={
        "descricao": "Descrição",
        "valor": "Valor",
        "valor_baixado": "Valor baixado",
        "data_vencimento": "Vencimento",
        "data_baixa": "Baixa",
        "status": "Status"
    })

    st.dataframe(
        receber_exibicao,
        width="stretch",
        hide_index=True
    )

st.caption("Versão 0.2 - Clientes multiempresa")