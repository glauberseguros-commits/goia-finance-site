
import streamlit as st
import pandas as pd
import sqlite3

DB_PATH = "bd/gofinance.db"
from utils.auth import empresa_logada, exigir_login

exigir_login()

EMPRESA_ID = empresa_logada()


st.set_page_config(page_title="Fornecedores", page_icon="🏭", layout="wide")

st.title("🏭 Fornecedores")
st.caption("Cadastro, consulta e visão financeira por fornecedor.")

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

aba1, aba2 = st.tabs(["Cadastrar fornecedor", "Consultar fornecedores"])

with aba1:
    st.subheader("Cadastro manual")

    with st.form("form_fornecedor"):
        nome = st.text_input("Nome / Razão Social")
        cnpj = st.text_input("CNPJ / CPF")
        categoria_padrao = st.text_input("Categoria padrão", value="A classificar")
        email = st.text_input("E-mail")
        telefone = st.text_input("Telefone")
        endereco = st.text_input("Endereço")
        cidade = st.text_input("Cidade")
        uf = st.text_input("UF")
        salvar = st.form_submit_button("Salvar fornecedor")

    if salvar:
        if not nome.strip():
            st.error("Informe o nome do fornecedor.")
        else:
            conn = conectar()
            cur = conn.cursor()

            cur.execute("""
            SELECT id FROM fornecedores
            WHERE empresa_id = ?
              AND (
                  cnpj = ?
                  OR nome = ?
              )
            """, (EMPRESA_ID, cnpj.strip(), nome.strip()))
            existe = cur.fetchone()

            if existe:
                st.warning("Fornecedor já cadastrado.")
            else:
                cur.execute("""
                INSERT INTO fornecedores (
                    empresa_id, nome, cnpj, categoria_padrao, tipo_padrao,
                    email, telefone, endereco, cidade, uf, origem_cadastro
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    EMPRESA_ID,
                    nome.strip(),
                    cnpj.strip(),
                    categoria_padrao.strip(),
                    "Pagar",
                    email.strip(),
                    telefone.strip(),
                    endereco.strip(),
                    cidade.strip(),
                    uf.strip(),
                    "Manual"
                ))
                conn.commit()
                st.success("Fornecedor cadastrado com sucesso.")

            conn.close()

with aba2:
    conn = conectar()

    fornecedores = pd.read_sql_query("""
    SELECT
        id,
        nome,
        cnpj,
        categoria_padrao,
        email,
        telefone,
        cidade,
        uf,
        status,
        origem_cadastro
    FROM fornecedores
    WHERE empresa_id = ?
    ORDER BY nome
    """, conn, params=(EMPRESA_ID,))

    conn.close()

    busca = st.text_input("Buscar fornecedor por nome ou CNPJ/CPF")

    if busca and not fornecedores.empty:
        mask = (
            fornecedores["nome"].fillna("").str.contains(busca, case=False, na=False)
            | fornecedores["cnpj"].fillna("").str.contains(busca, case=False, na=False)
        )
        fornecedores = fornecedores[mask]

    if fornecedores.empty:
        st.info("Nenhum fornecedor cadastrado.")
    else:
        st.dataframe(fornecedores.drop(columns=["id"]), width="stretch", hide_index=True)

        nomes = fornecedores["nome"].tolist()
        fornecedor_nome = st.selectbox("Selecionar fornecedor para detalhes", nomes)

        fornecedor_id = int(fornecedores[fornecedores["nome"] == fornecedor_nome]["id"].iloc[0])

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
              cnpj_emitente = (
                  SELECT cnpj FROM fornecedores WHERE id = ?
              )
              OR nome_emitente = (
                  SELECT nome FROM fornecedores WHERE id = ?
              )
          )
          AND direcao = 'Nota Fiscal de Compra'
        ORDER BY data_emissao DESC
        """, conn, params=(EMPRESA_ID, fornecedor_id, fornecedor_id))

        pagar = pd.read_sql_query("""
        SELECT
            descricao,
            categoria,
            valor,
            valor_baixado,
            data_vencimento,
            data_baixa,
            status,
            forma_pagamento,
            cartao_credito_id,
            conta_bancaria_id
        FROM contas_pagar
        WHERE empresa_id = ?
          AND fornecedor_id = ?
        ORDER BY data_vencimento DESC
        """, conn, params=(EMPRESA_ID, fornecedor_id))

        conn.close()

        st.divider()
        st.subheader(f"Detalhes do fornecedor: {fornecedor_nome}")

        c1, c2, c3 = st.columns(3)

        total_notas = notas["valor"].sum() if not notas.empty else 0
        total_pagar = pagar["valor"].sum() if not pagar.empty else 0
        total_pago = pagar["valor_baixado"].sum() if not pagar.empty else 0

        with c1:
            st.metric("Notas recebidas", moeda(total_notas))

        with c2:
            st.metric("Total a pagar", moeda(total_pagar))

        with c3:
            st.metric("Total pago/baixado", moeda(total_pago))

        st.markdown("### Notas fiscais recebidas")
        if notas.empty:
            st.info("Nenhuma NF-e de compra encontrada para este fornecedor.")
        else:
            notas["data_emissao"] = notas["data_emissao"].apply(data_br)
            notas["valor"] = notas["valor"].apply(moeda)
            st.dataframe(notas, width="stretch", hide_index=True)

        st.markdown("### Contas a pagar")
        if pagar.empty:
            st.info("Nenhuma conta a pagar encontrada para este fornecedor.")
        else:
            pagar["data_vencimento"] = pagar["data_vencimento"].apply(data_br)
            pagar["data_baixa"] = pagar["data_baixa"].apply(data_br)
            pagar["valor"] = pagar["valor"].apply(moeda)
            pagar["valor_baixado"] = pagar["valor_baixado"].apply(moeda)
            st.dataframe(pagar, width="stretch", hide_index=True)
