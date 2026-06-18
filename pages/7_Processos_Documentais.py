import streamlit as st
import pandas as pd
import sqlite3
from utils.formatadores import formatar_moeda, formatar_data, formatar_cnpj

DB_PATH = "bd/gofinance.db"
EMPRESA_ID_ATIVA = 1

st.set_page_config(
    page_title="Processos Documentais",
    page_icon="🗂️",
    layout="wide"
)

st.title("🗂️ Processos Documentais")
st.caption("Controle de documentos, pendências, evidências e encerramento financeiro.")


def carregar_processos():
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            pd.id,
            pd.titulo,
            pd.tipo_operacao,
            pd.papel_empresa,
            pd.natureza,
            pd.contraparte_nome,
            pd.contraparte_cnpj,
            pd.valor_total,
            pd.status,
            pd.proxima_acao,
            pd.criado_em,
            COUNT(pp.id) AS total_pendencias,
            SUM(CASE WHEN pp.status = 'Pendente' THEN 1 ELSE 0 END) AS pendencias_abertas
        FROM processos_documentais pd
        LEFT JOIN processo_pendencias pp
            ON pp.processo_id = pd.id
           AND pp.empresa_id = pd.empresa_id
        WHERE pd.empresa_id = ?
        GROUP BY
            pd.id,
            pd.titulo,
            pd.tipo_operacao,
            pd.papel_empresa,
            pd.natureza,
            pd.contraparte_nome,
            pd.contraparte_cnpj,
            pd.valor_total,
            pd.status,
            pd.proxima_acao,
            pd.criado_em
        ORDER BY pd.id DESC
    """

    df = pd.read_sql_query(query, conn, params=(EMPRESA_ID_ATIVA,))
    conn.close()
    return df

def carregar_documentos(processo_id):
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            pd.id,
            pd.tipo_documento,
            pd.obrigatorio,
            pd.status,
            d.id AS documento_id,
            d.tipo_documento AS tipo_origem,
            d.direcao,
            d.numero_nfe,
            d.serie_nfe,
            d.chave_acesso_nfe,
            d.valor,
            d.data_emissao
        FROM processo_documentos pd
        LEFT JOIN documentos d
            ON d.id = pd.documento_id
        WHERE pd.processo_id = ?
          AND pd.empresa_id = ?
        ORDER BY pd.id
    """

    df = pd.read_sql_query(query, conn, params=(processo_id, EMPRESA_ID_ATIVA))
    conn.close()
    return df

def carregar_pendencias(processo_id):
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            id,
            descricao,
            tipo_evidencia,
            status,
            prazo,
            documento_id,
            criado_em
        FROM processo_pendencias
        WHERE processo_id = ?
          AND empresa_id = ?
        ORDER BY
            CASE WHEN status = 'Pendente' THEN 0 ELSE 1 END,
            id
    """

    df = pd.read_sql_query(query, conn, params=(processo_id, EMPRESA_ID_ATIVA))
    conn.close()
    return df

def concluir_pendencia(pendencia_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        UPDATE processo_pendencias
        SET status = 'Concluída'
        WHERE id = ?
          AND empresa_id = ?
    """, (pendencia_id, EMPRESA_ID_ATIVA))

    conn.commit()
    conn.close()

def atualizar_status_processo(processo_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM processo_pendencias
        WHERE processo_id = ?
          AND empresa_id = ?
          AND status = 'Pendente'
    """, (processo_id, EMPRESA_ID_ATIVA))

    pendentes = cur.fetchone()[0]

    if pendentes == 0:
        cur.execute("""
            UPDATE processos_documentais
            SET status = 'Concluído',
                proxima_acao = 'Processo sem pendências abertas'
            WHERE id = ?
              AND empresa_id = ?
        """, (processo_id, EMPRESA_ID_ATIVA))
    else:
        cur.execute("""
            UPDATE processos_documentais
            SET status = 'Aberto'
            WHERE id = ?
              AND empresa_id = ?
        """, (processo_id, EMPRESA_ID_ATIVA))

    conn.commit()
    conn.close()

df = carregar_processos()

if df.empty:
    st.warning("Nenhum processo documental cadastrado ainda.")
    st.stop()

df["valor_total"] = pd.to_numeric(df["valor_total"], errors="coerce").fillna(0)
df["total_pendencias"] = pd.to_numeric(df["total_pendencias"], errors="coerce").fillna(0)
df["pendencias_abertas"] = pd.to_numeric(df["pendencias_abertas"], errors="coerce").fillna(0)

total_processos = len(df)
processos_abertos = len(df[df["status"] == "Aberto"])
pendencias_abertas = int(df["pendencias_abertas"].sum())
valor_em_processos = df["valor_total"].sum()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Processos", total_processos)

with col2:
    st.metric("Abertos", processos_abertos)

with col3:
    st.metric("Pendências", pendencias_abertas)

with col4:
    st.metric("Valor total", formatar_moeda(valor_em_processos))

st.divider()

col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    filtro_status = st.selectbox(
        "Filtrar por status",
        ["Todos"] + sorted(df["status"].dropna().unique().tolist())
    )

with col_f2:
    filtro_operacao = st.selectbox(
        "Filtrar por operação",
        ["Todos"] + sorted(df["tipo_operacao"].dropna().unique().tolist())
    )

with col_f3:
    filtro_natureza = st.selectbox(
        "Filtrar por natureza",
        ["Todos"] + sorted(df["natureza"].dropna().unique().tolist())
    )

df_filtrado = df.copy()

if filtro_status != "Todos":
    df_filtrado = df_filtrado[df_filtrado["status"] == filtro_status]

if filtro_operacao != "Todos":
    df_filtrado = df_filtrado[df_filtrado["tipo_operacao"] == filtro_operacao]

if filtro_natureza != "Todos":
    df_filtrado = df_filtrado[df_filtrado["natureza"] == filtro_natureza]

df_exibicao = df_filtrado.copy()
df_exibicao["valor_total"] = df_exibicao["valor_total"].apply(moeda)

df_exibicao = df_exibicao[[
    "id",
    "titulo",
    "tipo_operacao",
    "papel_empresa",
    "natureza",
    "contraparte_nome",
    "valor_total",
    "status",
    "pendencias_abertas",
    "proxima_acao"
]]

df_exibicao = df_exibicao.rename(columns={
    "id": "ID",
    "titulo": "Processo",
    "tipo_operacao": "Operação",
    "papel_empresa": "Papel",
    "natureza": "Natureza",
    "contraparte_nome": "Contraparte",
    "valor_total": "Valor",
    "status": "Status",
    "pendencias_abertas": "Pendências abertas",
    "proxima_acao": "Próxima ação"
})

st.dataframe(
    df_exibicao,
    width="stretch",
    hide_index=True
)

st.divider()

st.subheader("Detalhar processo")

ids = df_filtrado["id"].tolist()

if not ids:
    st.info("Nenhum processo encontrado com os filtros selecionados.")
    st.stop()

processo_id = st.selectbox("Selecione o ID do processo", ids)

processo = df[df["id"] == processo_id].iloc[0]

col_d1, col_d2, col_d3 = st.columns(3)

with col_d1:
    st.info(f"Processo: {processo['titulo']}")

with col_d2:
    st.info(f"Valor: {formatar_moeda(float(processo['valor_total']))}")

with col_d3:
    st.info(f"Status: {processo['status']}")

st.warning(f"Próxima ação: {processo['proxima_acao']}")

st.markdown("### Documentos vinculados")

df_docs = carregar_documentos(processo_id)

if df_docs.empty:
    st.warning("Nenhum documento vinculado a este processo.")
else:
    df_docs_exibicao = df_docs.copy()

    df_docs_exibicao["origem"] = df_docs_exibicao.apply(
        lambda r: f"NF-e {r['numero_nfe']}/Série {r['serie_nfe']}" if pd.notna(r["numero_nfe"]) and str(r["numero_nfe"]).strip() else r["tipo_origem"],
        axis=1
    )

    df_docs_exibicao["valor"] = pd.to_numeric(df_docs_exibicao["valor"], errors="coerce").fillna(0).apply(moeda)

    df_docs_exibicao = df_docs_exibicao[[
        "id",
        "tipo_documento",
        "origem",
        "direcao",
        "valor",
        "data_emissao",
        "status"
    ]]

    df_docs_exibicao = df_docs_exibicao.rename(columns={
        "id": "ID vínculo",
        "tipo_documento": "Tipo",
        "origem": "Origem",
        "direcao": "Direção",
        "valor": "Valor",
        "data_emissao": "Data",
        "status": "Status"
    })

    st.dataframe(
        df_docs_exibicao,
        width="stretch",
        hide_index=True
    )

st.markdown("### Pendências e evidências")

df_pend = carregar_pendencias(processo_id)

if df_pend.empty:
    st.success("Este processo não possui pendências.")
else:
    df_pend_exibicao = df_pend.copy()
    df_pend_exibicao["prazo"] = df_pend_exibicao["prazo"].apply(formatar_data)

    df_pend_exibicao = df_pend_exibicao[[
        "id",
        "descricao",
        "tipo_evidencia",
        "status",
        "prazo",
        "documento_id"
    ]]

    df_pend_exibicao = df_pend_exibicao.rename(columns={
        "id": "ID",
        "descricao": "Pendência",
        "tipo_evidencia": "Evidência exigida",
        "status": "Status",
        "prazo": "Prazo",
        "documento_id": "Documento evidência"
    })

    st.dataframe(
        df_pend_exibicao,
        width="stretch",
        hide_index=True
    )

    ids_pendentes = df_pend[df_pend["status"] == "Pendente"]["id"].tolist()

    if ids_pendentes:
        st.markdown("### Resolver pendência manualmente")

        pendencia_id = st.selectbox(
            "Selecione a pendência concluída",
            ids_pendentes
        )

        if st.button("Marcar pendência como concluída"):
            concluir_pendencia(int(pendencia_id))
            atualizar_status_processo(int(processo_id))
            st.success("Pendência concluída.")
            st.rerun()

st.caption("Versão 0.1 - Processos Documentais")
