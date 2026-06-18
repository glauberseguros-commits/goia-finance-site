import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from utils.formatadores import formatar_moeda, formatar_data

DB_PATH = "bd/gofinance.db"
EMPRESA_ID_ATIVA = 1

st.set_page_config(
    page_title="Importar Extrato",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 Importar Extrato Bancário")
st.caption("Importe extratos em CSV para gerar movimentos bancários e alimentar a conciliação.")

def garantir_colunas_csv(df):
    colunas = [c.lower().strip() for c in df.columns]
    df.columns = colunas

    obrigatorias = ["data", "historico", "valor"]
    faltantes = [c for c in obrigatorias if c not in df.columns]

    if faltantes:
        raise ValueError(f"CSV inválido. Colunas obrigatórias ausentes: {', '.join(faltantes)}")

    return df

def tipo_movimento(valor):
    return "Crédito" if float(valor) >= 0 else "Débito"

def importar_csv(nome_arquivo, df):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute("""
        INSERT INTO extratos_bancarios (
            conta_bancaria_id,
            nome_arquivo,
            periodo_inicio,
            periodo_fim,
            criado_em,
            empresa_id
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        1,
        nome_arquivo,
        str(df["data"].min()),
        str(df["data"].max()),
        agora,
        EMPRESA_ID_ATIVA
    ))

    extrato_id = cur.lastrowid

    inseridos = 0

    for _, row in df.iterrows():
        data_movimento = str(row["data"])
        historico = str(row["historico"])
        valor = float(str(row["valor"]).replace(".", "").replace(",", ".")) if isinstance(row["valor"], str) else float(row["valor"])
        tipo = tipo_movimento(valor)

        cur.execute("""
            INSERT INTO movimentos_bancarios (
                extrato_id,
                data_movimento,
                historico,
                valor,
                tipo,
                conciliado,
                criado_em,
                empresa_id,
                cnpj_origem,
                nome_origem
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            extrato_id,
            data_movimento,
            historico,
            valor,
            tipo,
            0,
            agora,
            EMPRESA_ID_ATIVA,
            str(row["cnpj_origem"]) if "cnpj_origem" in df.columns else "",
            str(row["nome_origem"]) if "nome_origem" in df.columns else ""
        ))

        inseridos += 1

    conn.commit()
    conn.close()

    return extrato_id, inseridos

st.markdown("### Modelo esperado do CSV")

st.code("""data,historico,valor,cnpj_origem,nome_origem
2026-06-18,PIX recebido cliente,2598.65,00394502007408,Estado-Maior da Armada
2026-06-18,PIX fornecedor,-2410.00,11222333000144,Ponto Certo Comercio
""")

arquivo = st.file_uploader(
    "Selecione o extrato bancário CSV",
    type=["csv"]
)

if arquivo:
    try:
        df = pd.read_csv(arquivo)
        df = garantir_colunas_csv(df)

        st.success("Arquivo lido com sucesso.")
        st.dataframe(df, width="stretch", hide_index=True)

        if st.button("Importar extrato"):
            extrato_id, inseridos = importar_csv(arquivo.name, df)
            st.success(f"Extrato importado. ID: {extrato_id}. Movimentos criados: {inseridos}.")

    except Exception as e:
        st.error(str(e))

st.divider()

st.subheader("Extratos importados")

conn = sqlite3.connect(DB_PATH)

df_ext = pd.read_sql_query("""
    SELECT
        id,
        nome_arquivo,
        periodo_inicio,
        periodo_fim,
        criado_em
    FROM extratos_bancarios
    WHERE empresa_id = ?
    ORDER BY id DESC
""", conn, params=(EMPRESA_ID_ATIVA,))

conn.close()

if df_ext.empty:
    st.info("Nenhum extrato importado ainda.")
else:
    for col in ["periodo_inicio", "periodo_fim", "criado_em"]:
        df_ext[col] = df_ext[col].fillna("").apply(formatar_data)

    df_ext = df_ext.rename(columns={
        "id": "ID",
        "nome_arquivo": "Arquivo",
        "periodo_inicio": "Início",
        "periodo_fim": "Fim",
        "criado_em": "Criado em"
    })

    st.dataframe(df_ext, width="stretch", hide_index=True)

st.caption("Versão 0.1 - Importação de Extrato Bancário")
