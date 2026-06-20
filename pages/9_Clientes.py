
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

aba1, aba2 = st.tabs(["Cadastrar cliente", "Consultar clientes"])

with aba1:
    st.subheader("Cadastro manual")

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

with aba2:
    conn = conectar()

    clientes = pd.read_sql_query("""
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
        st.dataframe(clientes.drop(columns=["id"]), width="stretch", hide_index=True)

        nomes = clientes["nome"].tolist()
        cliente_nome = st.selectbox("Selecionar cliente para detalhes", nomes)

        cliente_id = int(clientes[clientes["nome"] == cliente_nome]["id"].iloc[0])

        conn = conectar()

        notas = pd.read_sql_query("""
        SELECT
            numero_nfe,
            serie_nfe,
            data_emissao,
            valor,
            status_processamento
        FROM documentos
        WHERE empresa_id = ?
          AND (
              cnpj_destinatario = (
                  SELECT cnpj_cpf FROM clientes WHERE id = ?
              )
              OR nome_destinatario = (
                  SELECT nome FROM clientes WHERE id = ?
              )
          )
          AND direcao = 'Nota Fiscal de Venda'
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

        conn.close()

        st.divider()
        st.subheader(f"Detalhes do cliente: {cliente_nome}")

        c1, c2, c3 = st.columns(3)

        total_notas = notas["valor"].sum() if not notas.empty else 0
        total_receber = receber["valor"].sum() if not receber.empty else 0
        total_recebido = receber["valor_baixado"].sum() if not receber.empty else 0

        with c1:
            st.metric("Notas emitidas", moeda(total_notas))

        with c2:
            st.metric("Total a receber", moeda(total_receber))

        with c3:
            st.metric("Total recebido", moeda(total_recebido))

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
