import streamlit as st
import pandas as pd
import sqlite3
from utils.formatadores import formatar_moeda, formatar_data

DB_PATH = "bd/gofinance.db"
EMPRESA_ID_ATIVA = 1

st.set_page_config(
    page_title="Conciliação Bancária",
    page_icon="🔄",
    layout="wide"
)


st.markdown("""
<style>
[data-testid="stSidebarNav"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)


st.title("🔄 Conciliação Bancária")
st.caption("Cruzamento entre movimentos bancários, contas a pagar e contas a receber.")

def carregar_movimentos():
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query("""
        SELECT
            id,
            data_movimento,
            historico,
            valor,
            tipo,
            conciliado,
            cnpj_origem,
            nome_origem
        FROM movimentos_bancarios
        WHERE empresa_id = ?
        ORDER BY data_movimento DESC, id DESC
    """, conn, params=(EMPRESA_ID_ATIVA,))

    conn.close()
    return df

def carregar_receber_pendentes():
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query("""
        SELECT
            cr.id,
            cr.documento_id,
            COALESCE(c.nome, 'Cliente não identificado') AS contraparte,
            cr.descricao,
            cr.valor,
            cr.data_vencimento,
            cr.status
        FROM contas_receber cr
        LEFT JOIN clientes c ON c.id = cr.cliente_id
        WHERE cr.empresa_id = ?
          AND cr.status = 'Pendente'
        ORDER BY cr.data_vencimento ASC, cr.id ASC
    """, conn, params=(EMPRESA_ID_ATIVA,))

    conn.close()
    return df

def carregar_pagar_pendentes():
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query("""
        SELECT
            cp.id,
            cp.documento_id,
            COALESCE(f.nome, 'Fornecedor não identificado') AS contraparte,
            cp.descricao,
            cp.valor,
            cp.data_vencimento,
            cp.status
        FROM contas_pagar cp
        LEFT JOIN fornecedores f ON f.id = cp.fornecedor_id
        WHERE cp.empresa_id = ?
          AND cp.status = 'Pendente'
        ORDER BY cp.data_vencimento ASC, cp.id ASC
    """, conn, params=(EMPRESA_ID_ATIVA,))

    conn.close()
    return df

def gerar_sugestoes(df_mov, df_rec, df_pag):
    sugestoes = []

    for _, mov in df_mov[df_mov["conciliado"] == 0].iterrows():
        if mov["tipo"] == "Crédito":
            candidatos = df_rec.copy()
            tipo_conta = "Receber"
        else:
            candidatos = df_pag.copy()
            tipo_conta = "Pagar"

        if candidatos.empty:
            continue

        candidatos["diferenca"] = (candidatos["valor"] - abs(float(mov["valor"]))).abs()
        melhor = candidatos.sort_values("diferenca").iloc[0]

        score = 100 if melhor["diferenca"] < 0.01 else max(0, 80 - melhor["diferenca"])

        sugestoes.append({
            "movimento_id": int(mov["id"]),
            "data_movimento": mov["data_movimento"],
            "historico": mov["historico"],
            "tipo_movimento": mov["tipo"],
            "valor_movimento": float(mov["valor"]),
            "tipo_conta": tipo_conta,
            "conta_id": int(melhor["id"]),
            "contraparte": melhor["contraparte"],
            "descricao": melhor["descricao"],
            "valor_conta": float(melhor["valor"]),
            "diferenca": float(melhor["diferenca"]),
            "score": float(score)
        })

    return pd.DataFrame(sugestoes)

def conciliar(movimento_id, tipo_conta, conta_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    conta_pagar_id = conta_id if tipo_conta == "Pagar" else None
    conta_receber_id = conta_id if tipo_conta == "Receber" else None
    tipo_conciliacao = "Pagamento" if tipo_conta == "Pagar" else "Recebimento"

    cur.execute("""
        INSERT INTO conciliacoes (
            movimento_bancario_id,
            conta_pagar_id,
            conta_receber_id,
            tipo_conciliacao,
            empresa_id,
            status,
            score_match,
            criterios_match
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        movimento_id,
        conta_pagar_id,
        conta_receber_id,
        tipo_conciliacao,
        EMPRESA_ID_ATIVA,
        "Conciliado",
        100,
        "Valor + tipo de movimento"
    ))

    cur.execute("""
        UPDATE movimentos_bancarios
        SET conciliado = 1
        WHERE id = ?
          AND empresa_id = ?
    """, (movimento_id, EMPRESA_ID_ATIVA))

    conn.commit()
    conn.close()

df_mov = carregar_movimentos()
df_rec = carregar_receber_pendentes()
df_pag = carregar_pagar_pendentes()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Movimentos", len(df_mov))

with col2:
    st.metric("Não conciliados", len(df_mov[df_mov["conciliado"] == 0]) if not df_mov.empty else 0)

with col3:
    st.metric("Receber pendente", formatar_moeda(df_rec["valor"].sum() if not df_rec.empty else 0))

with col4:
    st.metric("Pagar pendente", formatar_moeda(df_pag["valor"].sum() if not df_pag.empty else 0))

st.divider()

st.subheader("Sugestões de conciliação")

df_sug = gerar_sugestoes(df_mov, df_rec, df_pag)

if df_sug.empty:
    st.info("Nenhuma sugestão de conciliação encontrada.")
else:
    df_show = df_sug.copy()

    df_show["data_movimento"] = df_show["data_movimento"].apply(formatar_data)
    df_show["valor_movimento"] = df_show["valor_movimento"].apply(formatar_moeda)
    df_show["valor_conta"] = df_show["valor_conta"].apply(formatar_moeda)
    df_show["diferenca"] = df_show["diferenca"].apply(formatar_moeda)

    df_show = df_show.rename(columns={
        "movimento_id": "Movimento ID",
        "data_movimento": "Data",
        "historico": "Histórico",
        "tipo_movimento": "Tipo mov.",
        "valor_movimento": "Valor mov.",
        "tipo_conta": "Tipo conta",
        "conta_id": "Conta ID",
        "contraparte": "Contraparte",
        "descricao": "Descrição",
        "valor_conta": "Valor conta",
        "diferenca": "Diferença",
        "score": "Score"
    })

    st.dataframe(df_show, width="stretch", hide_index=True)

    st.markdown("### Confirmar conciliação")

    opcoes = [
        f"Mov. {r.movimento_id} → {r.tipo_conta} {r.conta_id} | {r.contraparte} | {formatar_moeda(r.valor_conta)}"
        for r in df_sug.itertuples()
    ]

    escolha = st.selectbox("Selecione a sugestão", opcoes)
    idx = opcoes.index(escolha)
    linha = df_sug.iloc[idx]

    if st.button("Conciliar selecionado"):
        conciliar(
            int(linha["movimento_id"]),
            linha["tipo_conta"],
            int(linha["conta_id"])
        )
        st.success("Movimento conciliado.")
        st.rerun()

st.divider()

st.subheader("Movimentos bancários")

if df_mov.empty:
    st.warning("Nenhum movimento bancário cadastrado.")
else:
    df_mov_show = df_mov.copy()
    df_mov_show["data_movimento"] = df_mov_show["data_movimento"].apply(formatar_data)
    df_mov_show["valor"] = df_mov_show["valor"].apply(formatar_moeda)
    df_mov_show["conciliado"] = df_mov_show["conciliado"].apply(lambda x: "Sim" if x == 1 else "Não")

    df_mov_show = df_mov_show.rename(columns={
        "id": "ID",
        "data_movimento": "Data",
        "historico": "Histórico",
        "valor": "Valor",
        "tipo": "Tipo",
        "conciliado": "Conciliado",
        "cnpj_origem": "CNPJ Origem",
        "nome_origem": "Nome Origem"
    })

    st.dataframe(df_mov_show, width="stretch", hide_index=True)

st.caption("Versão 0.1 - Conciliação Bancária")