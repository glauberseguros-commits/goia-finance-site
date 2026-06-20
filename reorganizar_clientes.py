from pathlib import Path

p = Path("pages/9_Clientes.py")

novo = r'''
import streamlit as st
import pandas as pd
import sqlite3

DB_PATH = "bd/gofinance.db"
EMPRESA_ID = 1

st.set_page_config(page_title="Clientes", page_icon="👥", layout="wide")

st.title("👥 Clientes")
st.caption("Cadastro, consulta e visão financeira por cliente.")

def conectar():
    return sqlite3.connect(DB_PATH)

def moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def data_br(valor):
    if not valor:
        return ""
    try:
        return pd.to_datetime(valor).strftime("%d/%m/%Y")
    except:
        return valor

aba1, aba2, aba3 = st.tabs([
    "Consultar clientes",
    "Cadastrar manualmente",
    "Cadastrar por documento"
])

with aba1:
    st.subheader("Clientes cadastrados")

    conn = conectar()

    clientes = pd.read_sql_query("""
    SELECT
        c.id,
        c.nome,
        c.cnpj_cpf,
        c.email,
        c.telefone,
        c.cidade,
        c.uf,
        c.status,
        c.origem_cadastro,
        COALESCE(SUM(DISTINCT d.valor), 0) AS total_notas_emitidas,
        COALESCE(SUM(DISTINCT cr.valor), 0) AS total_a_receber,
        COALESCE(SUM(DISTINCT cr.valor_baixado), 0) AS total_recebido
    FROM clientes c
    LEFT JOIN documentos d
        ON d.empresa_id = c.empresa_id
       AND d.direcao = 'Nota Fiscal de Venda'
       AND (
            d.cnpj_destinatario = c.cnpj_cpf
            OR d.nome_destinatario = c.nome
       )
    LEFT JOIN contas_receber cr
        ON cr.empresa_id = c.empresa_id
       AND cr.cliente_id = c.id
    WHERE c.empresa_id = ?
    GROUP BY c.id
    ORDER BY c.nome
    """, conn, params=(EMPRESA_ID,))

    conn.close()

    busca = st.text_input("Buscar cliente por nome ou CNPJ/CPF")

    if busca and not clientes.empty:
        mask = (
            clientes["nome"].fillna("").str.contains(busca, case=False, na=False)
            | clientes["cnpj_cpf"].fillna("").str.contains(busca, case=False, na=False)
        )
        clientes = clientes[mask]

    if clientes.empty:
        st.info("Nenhum cliente cadastrado.")
    else:
        resumo = clientes.copy()
        resumo["total_notas_emitidas"] = resumo["total_notas_emitidas"].apply(moeda)
        resumo["total_a_receber"] = resumo["total_a_receber"].apply(moeda)
        resumo["total_recebido"] = resumo["total_recebido"].apply(moeda)

        st.dataframe(
            resumo.drop(columns=["id"]),
            width="stretch",
            hide_index=True
        )

        st.divider()

        cliente_nome = st.selectbox(
            "Selecionar cliente para análise financeira",
            clientes["nome"].tolist()
        )

        cliente_id = int(clientes[clientes["nome"] == cliente_nome]["id"].iloc[0])

        conn = conectar()

        notas = pd.read_sql_query("""
        SELECT
            numero_nfe AS nf,
            serie_nfe AS serie,
            data_emissao,
            valor,
            status_processamento AS status
        FROM documentos
        WHERE empresa_id = ?
          AND direcao = 'Nota Fiscal de Venda'
          AND (
              cnpj_destinatario = (
                  SELECT cnpj_cpf FROM clientes WHERE id = ?
              )
              OR nome_destinatario = (
                  SELECT nome FROM clientes WHERE id = ?
              )
          )
        ORDER BY data_emissao DESC
        """, conn, params=(EMPRESA_ID, cliente_id, cliente_id))

        receber = pd.read_sql_query("""
        SELECT
            descricao,
            categoria,
            valor,
            valor_baixado,
            data_vencimento,
            data_baixa,
            status,
            forma_recebimento
        FROM contas_receber
        WHERE empresa_id = ?
          AND cliente_id = ?
        ORDER BY data_vencimento DESC
        """, conn, params=(EMPRESA_ID, cliente_id))

        recebimentos = pd.read_sql_query("""
        SELECT
            data_movimento,
            historico,
            valor,
            tipo,
            conciliado
        FROM movimentos_bancarios
        WHERE empresa_id = ?
          AND (
              cnpj_origem = (
                  SELECT cnpj_cpf FROM clientes WHERE id = ?
              )
              OR nome_origem = (
                  SELECT nome FROM clientes WHERE id = ?
              )
          )
        ORDER BY data_movimento DESC
        """, conn, params=(EMPRESA_ID, cliente_id, cliente_id))

        conciliacoes = pd.read_sql_query("""
        SELECT
            co.data_conciliacao,
            co.tipo_conciliacao,
            co.status,
            co.score_match,
            co.criterios_match
        FROM conciliacoes co
        INNER JOIN contas_receber cr
            ON cr.id = co.conta_receber_id
           AND cr.empresa_id = co.empresa_id
        WHERE co.empresa_id = ?
          AND cr.cliente_id = ?
        ORDER BY co.data_conciliacao DESC
        """, conn, params=(EMPRESA_ID, cliente_id))

        conn.close()

        st.subheader(f"Análise do cliente: {cliente_nome}")

        total_notas = notas["valor"].sum() if not notas.empty else 0
        total_receber = receber["valor"].sum() if not receber.empty else 0
        total_recebido = receber["valor_baixado"].sum() if not receber.empty else 0
        saldo_aberto = total_receber - total_recebido

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric("NF emitidas", moeda(total_notas))

        with c2:
            st.metric("A receber", moeda(total_receber))

        with c3:
            st.metric("Recebido", moeda(total_recebido))

        with c4:
            st.metric("Saldo aberto", moeda(saldo_aberto))

        st.markdown("### Linha financeira do cliente")

        if notas.empty and receber.empty and recebimentos.empty:
            st.info("Ainda não há movimentação financeira vinculada a este cliente.")
        else:
            st.markdown("""
            **Fluxo esperado:** Cliente → NF-e de saída → Conta a receber → Recebimento bancário → Conciliação → Baixa
            """)

        st.markdown("### Notas fiscais emitidas")
        if notas.empty:
            st.info("Nenhuma NF-e de venda encontrada para este cliente.")
        else:
            notas["data_emissao"] = notas["data_emissao"].apply(data_br)
            notas["valor"] = notas["valor"].apply(moeda)
            st.dataframe(notas, width="stretch", hide_index=True)

        st.markdown("### Contas a receber")
        if receber.empty:
            st.info("Nenhuma conta a receber encontrada para este cliente.")
        else:
            receber["data_vencimento"] = receber["data_vencimento"].apply(data_br)
            receber["data_baixa"] = receber["data_baixa"].apply(data_br)
            receber["valor"] = receber["valor"].apply(moeda)
            receber["valor_baixado"] = receber["valor_baixado"].apply(moeda)
            st.dataframe(receber, width="stretch", hide_index=True)

        st.markdown("### Recebimentos bancários")
        if recebimentos.empty:
            st.info("Nenhum recebimento bancário identificado para este cliente.")
        else:
            recebimentos["data_movimento"] = recebimentos["data_movimento"].apply(data_br)
            recebimentos["valor"] = recebimentos["valor"].apply(moeda)
            recebimentos["conciliado"] = recebimentos["conciliado"].apply(lambda x: "Sim" if x else "Não")
            st.dataframe(recebimentos, width="stretch", hide_index=True)

        st.markdown("### Conciliações")
        if conciliacoes.empty:
            st.info("Nenhuma conciliação encontrada para este cliente.")
        else:
            conciliacoes["data_conciliacao"] = conciliacoes["data_conciliacao"].apply(data_br)
            conciliacoes["score_match"] = conciliacoes["score_match"].apply(lambda x: f"{float(x or 0):.0%}")
            st.dataframe(conciliacoes, width="stretch", hide_index=True)

with aba2:
    st.subheader("Cadastro manual de cliente")

    with st.form("form_cliente"):
        nome = st.text_input("Nome / Razão Social")
        cnpj_cpf = st.text_input("CNPJ / CPF")
        email = st.text_input("E-mail")
        telefone = st.text_input("Telefone")
        endereco = st.text_input("Endereço")
        cidade = st.text_input("Cidade")
        uf = st.text_input("UF")
        salvar = st.form_submit_button("Salvar cliente")

    if salvar:
        if not nome.strip():
            st.error("Informe o nome do cliente.")
        else:
            conn = conectar()
            cur = conn.cursor()

            cur.execute("""
            SELECT id FROM clientes
            WHERE empresa_id = ?
              AND (
                  cnpj_cpf = ?
                  OR nome = ?
              )
            """, (EMPRESA_ID, cnpj_cpf.strip(), nome.strip()))
            existe = cur.fetchone()

            if existe:
                st.warning("Cliente já cadastrado.")
            else:
                cur.execute("""
                INSERT INTO clientes (
                    empresa_id, nome, cnpj_cpf, email, telefone, endereco, cidade, uf, origem_cadastro
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    EMPRESA_ID,
                    nome.strip(),
                    cnpj_cpf.strip(),
                    email.strip(),
                    telefone.strip(),
                    endereco.strip(),
                    cidade.strip(),
                    uf.strip(),
                    "Manual"
                ))
                conn.commit()
                st.success("Cliente cadastrado com sucesso.")

            conn.close()

with aba3:
    st.subheader("Cadastro por documento")
    st.info("Aqui entraremos com PDF, XML, CSV ou NF-e de saída para cadastrar/atualizar clientes automaticamente.")
    st.write("Regra: se o documento for NF-e de saída, o destinatário é tratado como cliente.")
'''

p.write_text(novo, encoding="utf-8")
print("OK - página Clientes reorganizada.")
