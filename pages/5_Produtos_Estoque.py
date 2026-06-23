from utils.db import caminho_banco, conectar_banco
import streamlit as st
from utils.ui import aplicar_estilo_premium
import pandas as pd
import sqlite3
from utils.formatadores import formatar_data
from utils.auth import empresa_logada, exigir_login

DB_PATH = caminho_banco()

exigir_login()
EMPRESA_ID_ATIVA = empresa_logada()

st.set_page_config(
    page_title="Produtos / Estoque",
    page_icon="📦",
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
    st.sidebar.page_link("pages/5_Produtos_Estoque.py", label="Produtos / Estoque", icon="📦")
    st.sidebar.page_link("pages/6_Vendas.py", label="Vendas", icon="🧾")
    st.sidebar.page_link("pages/7_Processos_Documentais.py", label="Processos Documentais", icon="🗂️")
    st.sidebar.page_link("pages/8_Conciliacao_Bancaria.py", label="Conciliação Bancária", icon="🏦")


menu_goia()

st.title("📦 Produtos / Estoque")
st.caption("Produtos cadastrados, custo, preço de venda e saldo em estoque.")


def moeda(valor):
    try:
        valor = float(valor or 0)
    except Exception:
        valor = 0.0

    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def numero_br(valor):
    try:
        valor = float(valor or 0)
    except Exception:
        valor = 0.0

    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def carregar_produtos():
    conn = conectar_banco()

    query = """
        SELECT
            p.id,
            p.descricao,
            p.categoria,
            p.custo_medio,
            p.preco_venda,
            p.criado_em,
            COALESCE(SUM(
                CASE
                    WHEN em.tipo = 'Entrada' THEN em.quantidade
                    WHEN em.tipo = 'Saída' THEN -em.quantidade
                    WHEN em.tipo = 'Saida' THEN -em.quantidade
                    ELSE 0
                END
            ), 0) AS saldo_estoque
        FROM produtos p
        LEFT JOIN estoque_movimentacoes em
            ON em.produto_id = p.id
           AND em.empresa_id = p.empresa_id
        WHERE p.empresa_id = ?
        GROUP BY
            p.id,
            p.descricao,
            p.categoria,
            p.custo_medio,
            p.preco_venda,
            p.criado_em
        ORDER BY p.descricao
    """

    df = pd.read_sql_query(query, conn, params=(EMPRESA_ID_ATIVA,))
    conn.close()
    return df


def carregar_movimentos(produto_id):
    conn = conectar_banco()

    query = """
        SELECT
            em.id,
            em.tipo,
            em.quantidade,
            em.valor_unitario,
            em.valor_total,
            em.origem,
            em.documento_id,
            d.numero_nfe,
            d.serie_nfe,
            em.data_movimento,
            em.criado_em
        FROM estoque_movimentacoes em
        LEFT JOIN documentos d
            ON d.id = em.documento_id
           AND d.empresa_id = em.empresa_id
        WHERE em.produto_id = ?
          AND em.empresa_id = ?
        ORDER BY em.data_movimento DESC, em.id DESC
    """

    df = pd.read_sql_query(query, conn, params=(produto_id, EMPRESA_ID_ATIVA))
    conn.close()
    return df


df = carregar_produtos()

if df.empty:
    st.warning("Nenhum produto cadastrado ainda.")
    st.stop()

df["custo_medio"] = pd.to_numeric(df["custo_medio"], errors="coerce").fillna(0)
df["preco_venda"] = pd.to_numeric(df["preco_venda"], errors="coerce").fillna(0)
df["saldo_estoque"] = pd.to_numeric(df["saldo_estoque"], errors="coerce").fillna(0)
df["categoria"] = df["categoria"].fillna("A classificar")

total_produtos = len(df)
valor_estoque_custo = (df["saldo_estoque"] * df["custo_medio"]).sum()
qtd_em_estoque = df["saldo_estoque"].sum()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Produtos cadastrados", total_produtos)

with col2:
    st.metric("Qtd. em estoque", numero_br(qtd_em_estoque))

with col3:
    st.metric("Estoque a custo", moeda(valor_estoque_custo))

st.divider()

col_f1, col_f2 = st.columns(2)

with col_f1:
    filtro_categoria = st.selectbox(
        "Filtrar por categoria",
        ["Todas"] + sorted(df["categoria"].dropna().unique().tolist())
    )

with col_f2:
    filtro_status_estoque = st.selectbox(
        "Filtrar por estoque",
        ["Todos", "Com estoque", "Sem estoque", "Estoque negativo"]
    )

df_filtrado = df.copy()

if filtro_categoria != "Todas":
    df_filtrado = df_filtrado[df_filtrado["categoria"] == filtro_categoria]

if filtro_status_estoque == "Com estoque":
    df_filtrado = df_filtrado[df_filtrado["saldo_estoque"] > 0]
elif filtro_status_estoque == "Sem estoque":
    df_filtrado = df_filtrado[df_filtrado["saldo_estoque"] == 0]
elif filtro_status_estoque == "Estoque negativo":
    df_filtrado = df_filtrado[df_filtrado["saldo_estoque"] < 0]

df_exibicao = df_filtrado.copy()

df_exibicao["saldo_estoque"] = df_exibicao["saldo_estoque"].apply(numero_br)
df_exibicao["custo_medio"] = df_exibicao["custo_medio"].apply(moeda)
df_exibicao["preco_venda"] = df_exibicao["preco_venda"].apply(moeda)
df_exibicao["criado_em"] = df_exibicao["criado_em"].fillna("").apply(formatar_data)

df_exibicao = df_exibicao[[
    "id",
    "descricao",
    "categoria",
    "saldo_estoque",
    "custo_medio",
    "preco_venda",
    "criado_em"
]]

df_exibicao = df_exibicao.rename(columns={
    "id": "ID",
    "descricao": "Produto",
    "categoria": "Categoria",
    "saldo_estoque": "Saldo estoque",
    "custo_medio": "Custo médio",
    "preco_venda": "Preço venda",
    "criado_em": "Criado em"
})

st.dataframe(
    df_exibicao,
    width="stretch",
    hide_index=True
)

st.divider()

st.subheader("Detalhar produto")

ids = df_filtrado["id"].tolist()

if not ids:
    st.info("Nenhum produto encontrado com os filtros selecionados.")
    st.stop()

produto_id = st.selectbox("Selecione o ID do produto", ids)

produto = df[df["id"] == produto_id].iloc[0]

col_d1, col_d2, col_d3 = st.columns(3)

with col_d1:
    st.info(f"Produto: {produto['descricao']}")

with col_d2:
    st.info(f"Saldo: {numero_br(produto['saldo_estoque'])}")

with col_d3:
    st.info(f"Custo médio: {moeda(float(produto['custo_medio']))}")

st.markdown("### Editar produto")

with st.form("editar_produto"):
    nova_descricao = st.text_input(
        "Descrição",
        value=str(produto["descricao"] or "")
    )

    nova_categoria = st.text_input(
        "Categoria",
        value=str(produto["categoria"] or "")
    )

    novo_preco_venda = st.number_input(
        "Preço de venda",
        min_value=0.0,
        value=float(produto["preco_venda"] or 0),
        step=0.01
    )

    salvar_produto = st.form_submit_button("Salvar alterações")

if salvar_produto:
    conn = conectar_banco()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE produtos
        SET
            descricao = ?,
            categoria = ?,
            preco_venda = ?
        WHERE id = ?
          AND empresa_id = ?
    """, (
        nova_descricao,
        nova_categoria,
        novo_preco_venda,
        int(produto_id),
        EMPRESA_ID_ATIVA
    ))

    conn.commit()
    conn.close()

    st.success("Produto atualizado com sucesso.")
    st.rerun()

st.markdown("### Movimentações de estoque")

df_mov = carregar_movimentos(produto_id)

if df_mov.empty:
    st.warning("Nenhuma movimentação de estoque para este produto.")
else:
    df_mov_exibicao = df_mov.copy()

    def montar_origem(row):
        numero = row.get("numero_nfe")
        serie = row.get("serie_nfe")

        if pd.notna(numero) and str(numero).strip():
            if pd.notna(serie) and str(serie).strip():
                return f"NF-e {numero}/Série {serie}"
            return f"NF-e {numero}"

        return row.get("origem", "Movimentação")

    df_mov_exibicao["origem_fiscal"] = df_mov_exibicao.apply(montar_origem, axis=1)

    df_mov_exibicao["quantidade"] = pd.to_numeric(
        df_mov_exibicao["quantidade"],
        errors="coerce"
    ).fillna(0).apply(numero_br)

    df_mov_exibicao["valor_unitario"] = pd.to_numeric(
        df_mov_exibicao["valor_unitario"],
        errors="coerce"
    ).fillna(0).apply(moeda)

    df_mov_exibicao["valor_total"] = pd.to_numeric(
        df_mov_exibicao["valor_total"],
        errors="coerce"
    ).fillna(0).apply(moeda)

    df_mov_exibicao["data_movimento"] = df_mov_exibicao["data_movimento"].fillna("").apply(formatar_data)

    df_mov_exibicao = df_mov_exibicao[[
        "id",
        "tipo",
        "quantidade",
        "valor_unitario",
        "valor_total",
        "origem_fiscal",
        "data_movimento"
    ]]

    df_mov_exibicao = df_mov_exibicao.rename(columns={
        "id": "ID",
        "tipo": "Tipo",
        "quantidade": "Quantidade",
        "valor_unitario": "Valor unitário",
        "valor_total": "Valor total",
        "origem_fiscal": "Origem",
        "data_movimento": "Data"
    })

    st.dataframe(
        df_mov_exibicao,
        width="stretch",
        hide_index=True
    )

st.caption("Versão 0.2 - Produtos / Estoque multiempresa")