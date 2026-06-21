import streamlit as st
import pandas as pd
import sqlite3

DB_PATH = "bd/gofinance.db"
EMPRESA_ID_ATIVA = 1

st.set_page_config(
    page_title="Produtos / Estoque",
    page_icon="📦",
    layout="wide"
)


st.markdown("""
<style>
[data-testid="stSidebarNav"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)


st.title("📦 Produtos / Estoque")
st.caption("Produtos cadastrados, custo, preço de venda e saldo em estoque.")

def moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def carregar_produtos():
    conn = sqlite3.connect(DB_PATH)

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
    conn = sqlite3.connect(DB_PATH)

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

total_produtos = len(df)
valor_estoque_custo = (df["saldo_estoque"] * df["custo_medio"]).sum()
qtd_em_estoque = df["saldo_estoque"].sum()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Produtos cadastrados", total_produtos)

with col2:
    st.metric("Qtd. em estoque", f"{qtd_em_estoque:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

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
df_exibicao["custo_medio"] = df_exibicao["custo_medio"].apply(moeda)
df_exibicao["preco_venda"] = df_exibicao["preco_venda"].apply(moeda)

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
    st.info(f"Saldo: {produto['saldo_estoque']}")

with col_d3:
    st.info(f"Custo médio: {moeda(float(produto['custo_medio']))}")

st.markdown("### Editar produto")

with st.form("editar_produto"):
    nova_descricao = st.text_input(
        "Descrição",
        value=str(produto["descricao"])
    )

    nova_categoria = st.text_input(
        "Categoria",
        value=str(produto["categoria"])
    )

    novo_preco_venda = st.number_input(
        "Preço de venda",
        min_value=0.0,
        value=float(produto["preco_venda"]),
        step=0.01
    )

    salvar_produto = st.form_submit_button("Salvar alterações")

if salvar_produto:
    conn = sqlite3.connect(DB_PATH)
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

    df_mov_exibicao["origem_fiscal"] = df_mov_exibicao.apply(
        lambda r: f"NF-e {r['numero_nfe']}/Série {r['serie_nfe']}" if pd.notna(r["numero_nfe"]) and str(r["numero_nfe"]).strip() else r["origem"],
        axis=1
    )

    df_mov_exibicao["valor_unitario"] = df_mov_exibicao["valor_unitario"].apply(moeda)
    df_mov_exibicao["valor_total"] = df_mov_exibicao["valor_total"].apply(moeda)

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

st.caption("Versão 0.1 - Produtos / Estoque")