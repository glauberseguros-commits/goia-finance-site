
import streamlit as st
import pandas as pd
import sqlite3

DB_PATH = "bd/gofinance.db"
EMPRESA_ID = 1

st.set_page_config(
    page_title="Central de Investigação",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Central de Investigação Financeira")
st.caption("Fila operacional para investigar movimentos bancários, identificar cliente/fornecedor, localizar documentos, sugerir conciliação e apontar pendências.")

def conectar():
    return sqlite3.connect(DB_PATH)

def moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def data_br(valor):
    if valor is None or valor == "":
        return ""
    try:
        return pd.to_datetime(valor).strftime("%d/%m/%Y")
    except:
        return valor

conn = conectar()

df = pd.read_sql_query("""
SELECT
    i.id,
    i.data_movimento,
    i.tipo_movimento,
    i.valor,
    i.nome_origem,
    i.cnpj_origem,
    COALESCE(c.nome, f.nome, 'Não identificado') AS pessoa_identificada,
    i.status_investigacao,
    i.diagnostico,
    i.acao_sugerida,
    i.score_match
FROM investigacoes_financeiras i
LEFT JOIN clientes c ON c.id = i.cliente_id AND c.empresa_id = i.empresa_id
LEFT JOIN fornecedores f ON f.id = i.fornecedor_id AND f.empresa_id = i.empresa_id
WHERE i.empresa_id = ?
ORDER BY i.id DESC
""", conn, params=(EMPRESA_ID,))

conn.close()

total = len(df)
pendentes = len(df[df["status_investigacao"] == "Pendente"]) if not df.empty else 0
resolvidos = len(df[df["status_investigacao"] == "Resolvido"]) if not df.empty else 0

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Movimentos investigados", total)

with c2:
    st.metric("Pendentes", pendentes)

with c3:
    st.metric("Resolvidos", resolvidos)

st.divider()

if df.empty:
    st.info("Nenhum movimento bancário encontrado para investigação.")
else:
    for _, row in df.iterrows():
        status = row["status_investigacao"]

        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([1.2, 1.2, 1.4, 1])

            with col1:
                st.markdown(f"### {row['tipo_movimento']}")
                st.write(data_br(row["data_movimento"]))

            with col2:
                st.markdown("### " + moeda(row["valor"]))
                st.write(row["nome_origem"] or "Origem não informada")

            with col3:
                st.write("**Identificação:**")
                st.write(row["pessoa_identificada"])
                if row["cnpj_origem"]:
                    st.write(row["cnpj_origem"])

            with col4:
                st.write("**Status:**")
                if status == "Resolvido":
                    st.success(status)
                else:
                    st.warning(status)

            st.write("**Diagnóstico:**")
            st.write(row["diagnostico"])

            st.write("**Ação sugerida:**")
            st.write(row["acao_sugerida"])

            st.progress(float(row["score_match"] or 0))
