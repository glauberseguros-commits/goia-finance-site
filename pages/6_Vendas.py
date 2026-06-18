import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

DB_PATH = "bd/gofinance.db"
EMPRESA_ID_ATIVA = 1

st.set_page_config(
    page_title="Vendas",
    page_icon="🧾",
    layout="wide"
)

st.title("🧾 Vendas")
st.caption("Registrar venda, baixar estoque e gerar conta a receber.")

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
            p.preco_venda
        ORDER BY p.descricao
    """

    df = pd.read_sql_query(query, conn, params=(EMPRESA_ID_ATIVA,))
    conn.close()

    if not df.empty:
        df["custo_medio"] = pd.to_numeric(df["custo_medio"], errors="coerce").fillna(0)
        df["preco_venda"] = pd.to_numeric(df["preco_venda"], errors="coerce").fillna(0)
        df["saldo_estoque"] = pd.to_numeric(df["saldo_estoque"], errors="coerce").fillna(0)

    return df

def obter_ou_criar_cliente(cursor, nome, cnpj_cpf=""):
    nome = (nome or "").strip()
    cnpj_cpf = (cnpj_cpf or "").strip()

    if cnpj_cpf:
        cursor.execute("""
            SELECT id
            FROM clientes
            WHERE cnpj_cpf = ?
              AND empresa_id = ?
        """, (cnpj_cpf, EMPRESA_ID_ATIVA))
    else:
        cursor.execute("""
            SELECT id
            FROM clientes
            WHERE nome = ?
              AND empresa_id = ?
        """, (nome, EMPRESA_ID_ATIVA))

    resultado = cursor.fetchone()

    if resultado:
        return resultado[0]

    cursor.execute("""
        INSERT INTO clientes (
            cnpj_cpf,
            nome,
            empresa_id
        )
        VALUES (?, ?, ?)
    """, (
        cnpj_cpf,
        nome,
        EMPRESA_ID_ATIVA
    ))

    return cursor.lastrowid

def registrar_venda(cliente_nome, cliente_cnpj, produto, quantidade, valor_unitario, data_venda, vencimento):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cliente_id = obter_ou_criar_cliente(cursor, cliente_nome, cliente_cnpj)

        descricao = produto["descricao"]
        produto_id = int(produto["id"])
        saldo_atual = float(produto["saldo_estoque"])
        quantidade = float(quantidade)
        valor_unitario = float(valor_unitario)
        valor_total = quantidade * valor_unitario

        if quantidade <= 0:
            raise ValueError("Quantidade deve ser maior que zero.")

        if quantidade > saldo_atual:
            raise ValueError(f"Estoque insuficiente. Saldo atual: {saldo_atual}")

        cursor.execute("""
            INSERT INTO vendas (
                cliente_id,
                documento_id,
                descricao,
                valor_total,
                data_venda,
                status,
                empresa_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            cliente_id,
            None,
            descricao,
            valor_total,
            data_venda,
            "Aberta",
            EMPRESA_ID_ATIVA
        ))

        venda_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO vendas_itens (
                venda_id,
                produto_id,
                descricao,
                quantidade,
                valor_unitario,
                valor_total,
                empresa_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            venda_id,
            produto_id,
            descricao,
            quantidade,
            valor_unitario,
            valor_total,
            EMPRESA_ID_ATIVA
        ))

        cursor.execute("""
            INSERT INTO estoque_movimentacoes (
                produto_id,
                tipo,
                quantidade,
                valor_unitario,
                valor_total,
                origem,
                documento_id,
                data_movimento,
                empresa_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            produto_id,
            "Saída",
            quantidade,
            valor_unitario,
            valor_total,
            f"Venda #{venda_id}",
            None,
            data_venda,
            EMPRESA_ID_ATIVA
        ))

        cursor.execute("""
            INSERT INTO contas_receber (
                cliente_id,
                documento_id,
                descricao,
                categoria,
                valor,
                data_emissao,
                data_vencimento,
                status,
                empresa_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cliente_id,
            None,
            descricao,
            "Vendas",
            valor_total,
            data_venda,
            vencimento,
            "Pendente",
            EMPRESA_ID_ATIVA
        ))

        conn.commit()

        return {
            "sucesso": True,
            "venda_id": venda_id,
            "valor_total": valor_total
        }

    except Exception as e:
        conn.rollback()
        return {
            "sucesso": False,
            "erro": str(e)
        }

    finally:
        conn.close()

df_produtos = carregar_produtos()

if df_produtos.empty:
    st.warning("Nenhum produto cadastrado para venda.")
    st.stop()

produtos_com_estoque = df_produtos[df_produtos["saldo_estoque"] > 0].copy()

if produtos_com_estoque.empty:
    st.warning("Não há produtos com estoque disponível para venda.")
    st.stop()

st.subheader("Nova venda")

with st.form("nova_venda"):
    col1, col2 = st.columns(2)

    with col1:
        cliente_nome = st.text_input("Cliente", value="Cliente não identificado")

    with col2:
        cliente_cnpj = st.text_input("CPF / CNPJ do cliente", value="")

    produto_opcao = st.selectbox(
        "Produto",
        produtos_com_estoque["id"].tolist(),
        format_func=lambda x: produtos_com_estoque[produtos_com_estoque["id"] == x]["descricao"].iloc[0]
    )

    produto = produtos_com_estoque[produtos_com_estoque["id"] == produto_opcao].iloc[0]

    colp1, colp2, colp3 = st.columns(3)

    with colp1:
        st.info(f"Estoque atual: {produto['saldo_estoque']}")

    with colp2:
        st.info(f"Custo médio: {moeda(float(produto['custo_medio']))}")

    with colp3:
        st.info(f"Preço venda atual: {moeda(float(produto['preco_venda']))}")

    colv1, colv2, colv3 = st.columns(3)

    with colv1:
        quantidade = st.number_input(
            "Quantidade",
            min_value=0.01,
            max_value=float(produto["saldo_estoque"]),
            value=1.0,
            step=1.0
        )

    with colv2:
        preco_padrao = float(produto["preco_venda"]) if float(produto["preco_venda"]) > 0 else float(produto["custo_medio"])
        valor_unitario = st.number_input(
            "Valor unitário",
            min_value=0.0,
            value=preco_padrao,
            step=0.01
        )

    with colv3:
        valor_total = quantidade * valor_unitario
        st.info(f"Total: {moeda(valor_total)}")

    coldata1, coldata2 = st.columns(2)

    with coldata1:
        data_venda = st.date_input("Data da venda", value=date.today())

    with coldata2:
        vencimento = st.date_input("Vencimento", value=date.today())

    confirmar = st.form_submit_button("Registrar venda")

if confirmar:
    resultado = registrar_venda(
        cliente_nome,
        cliente_cnpj,
        produto,
        quantidade,
        valor_unitario,
        data_venda.strftime("%Y-%m-%d"),
        vencimento.strftime("%Y-%m-%d")
    )

    if resultado["sucesso"]:
        st.success(
            f"Venda registrada com sucesso. Venda ID: {resultado['venda_id']}. "
            f"Valor: {moeda(resultado['valor_total'])}. Estoque baixado e conta a receber criada."
        )
        st.rerun()
    else:
        st.error(f"Erro ao registrar venda: {resultado['erro']}")

st.divider()

st.subheader("Produtos disponíveis")

df_exibicao = produtos_com_estoque.copy()
df_exibicao["custo_medio"] = df_exibicao["custo_medio"].apply(moeda)
df_exibicao["preco_venda"] = df_exibicao["preco_venda"].apply(moeda)

df_exibicao = df_exibicao[[
    "id",
    "descricao",
    "categoria",
    "saldo_estoque",
    "custo_medio",
    "preco_venda"
]]

df_exibicao = df_exibicao.rename(columns={
    "id": "ID",
    "descricao": "Produto",
    "categoria": "Categoria",
    "saldo_estoque": "Estoque",
    "custo_medio": "Custo médio",
    "preco_venda": "Preço venda"
})

st.dataframe(
    df_exibicao,
    width="stretch",
    hide_index=True
)

st.caption("Versão 0.1 - Vendas")
