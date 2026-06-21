import streamlit as st
from utils.ui import aplicar_estilo_premium
import pandas as pd
import sqlite3
from utils.formatadores import formatar_moeda, formatar_data
from utils.auth import empresa_logada, exigir_login

DB_PATH = "bd/gofinance.db"

exigir_login()
EMPRESA_ID_ATIVA = empresa_logada()

st.set_page_config(
    page_title="Processos Documentais",
    page_icon="🗂️",
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
           AND d.empresa_id = pd.empresa_id
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


def carregar_evidencias(processo_id):
    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            pe.id,
            pe.tipo_evidencia,
            pe.descricao,
            pe.valor,
            pe.data_evidencia,
            pe.origem,
            pe.status,
            pe.criado_em,
            d.tipo_documento,
            d.direcao,
            d.numero_nfe,
            d.serie_nfe
        FROM processo_evidencias pe
        LEFT JOIN documentos d
            ON d.id = pe.documento_id
           AND d.empresa_id = pe.empresa_id
        WHERE pe.processo_id = ?
          AND pe.empresa_id = ?
        ORDER BY pe.id
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
df["status"] = df["status"].fillna("Aberto")
df["tipo_operacao"] = df["tipo_operacao"].fillna("A classificar")
df["natureza"] = df["natureza"].fillna("A classificar")
df["proxima_acao"] = df["proxima_acao"].fillna("Sem próxima ação definida")


def calcular_situacao_goia(row):
    pendencias = int(row.get("pendencias_abertas", 0) or 0)
    status = str(row.get("status", ""))

    if pendencias > 0:
        return f"⚠️ Pendente: {pendencias} documento(s)"

    if status == "Concluído":
        return "✅ Processo completo"

    return "🟡 Aguardando validação"


df["situacao_goia"] = df.apply(calcular_situacao_goia, axis=1)

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
df_exibicao["valor_total"] = df_exibicao["valor_total"].apply(formatar_moeda)
df_exibicao["criado_em"] = df_exibicao["criado_em"].fillna("").apply(formatar_data)

df_exibicao = df_exibicao[[
    "id",
    "titulo",
    "tipo_operacao",
    "papel_empresa",
    "natureza",
    "contraparte_nome",
    "valor_total",
    "status",
    "situacao_goia",
    "pendencias_abertas",
    "proxima_acao",
    "criado_em"
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
    "situacao_goia": "Situação GOIA",
    "pendencias_abertas": "Pendências abertas",
    "proxima_acao": "Próxima ação",
    "criado_em": "Criado em"
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

    def montar_origem_documento(row):
        numero = row.get("numero_nfe")
        serie = row.get("serie_nfe")

        if pd.notna(numero) and str(numero).strip():
            if pd.notna(serie) and str(serie).strip():
                return f"NF-e {numero}/Série {serie}"
            return f"NF-e {numero}"

        return row.get("tipo_origem", "Documento")

    df_docs_exibicao["origem"] = df_docs_exibicao.apply(montar_origem_documento, axis=1)
    df_docs_exibicao["valor"] = pd.to_numeric(df_docs_exibicao["valor"], errors="coerce").fillna(0).apply(formatar_moeda)
    df_docs_exibicao["data_emissao"] = df_docs_exibicao["data_emissao"].fillna("").apply(formatar_data)

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

st.markdown("### Evidências vinculadas")

df_evid = carregar_evidencias(processo_id)

if df_evid.empty:
    st.info("Nenhuma evidência vinculada a este processo.")
else:
    df_evid_exibicao = df_evid.copy()

    def montar_origem_evidencia(row):
        numero = row.get("numero_nfe")
        serie = row.get("serie_nfe")

        if pd.notna(numero) and str(numero).strip():
            if pd.notna(serie) and str(serie).strip():
                return f"NF-e {numero}/Série {serie}"
            return f"NF-e {numero}"

        origem = row.get("origem")
        tipo_documento = row.get("tipo_documento")

        if pd.notna(origem) and str(origem).strip():
            return origem

        if pd.notna(tipo_documento) and str(tipo_documento).strip():
            return tipo_documento

        return "Evidência"

    df_evid_exibicao["origem_exibicao"] = df_evid_exibicao.apply(montar_origem_evidencia, axis=1)
    df_evid_exibicao["valor"] = pd.to_numeric(df_evid_exibicao["valor"], errors="coerce").fillna(0).apply(formatar_moeda)
    df_evid_exibicao["data_evidencia"] = df_evid_exibicao["data_evidencia"].fillna("").apply(formatar_data)
    df_evid_exibicao["criado_em"] = df_evid_exibicao["criado_em"].fillna("").apply(formatar_data)

    df_evid_exibicao = df_evid_exibicao[[
        "id",
        "tipo_evidencia",
        "descricao",
        "origem_exibicao",
        "valor",
        "data_evidencia",
        "status",
        "criado_em"
    ]]

    df_evid_exibicao = df_evid_exibicao.rename(columns={
        "id": "ID",
        "tipo_evidencia": "Tipo",
        "descricao": "Descrição",
        "origem_exibicao": "Origem",
        "valor": "Valor",
        "data_evidencia": "Data evidência",
        "status": "Status",
        "criado_em": "Criado em"
    })

    st.dataframe(
        df_evid_exibicao,
        width="stretch",
        hide_index=True
    )

st.markdown("### Pendências")

df_pend = carregar_pendencias(processo_id)

if df_pend.empty:
    st.success("Este processo não possui pendências.")
else:
    df_pend_exibicao = df_pend.copy()
    df_pend_exibicao["prazo"] = df_pend_exibicao["prazo"].fillna("").apply(formatar_data)
    df_pend_exibicao["criado_em"] = df_pend_exibicao["criado_em"].fillna("").apply(formatar_data)

    df_pend_exibicao = df_pend_exibicao[[
        "id",
        "descricao",
        "tipo_evidencia",
        "status",
        "prazo",
        "documento_id",
        "criado_em"
    ]]

    df_pend_exibicao = df_pend_exibicao.rename(columns={
        "id": "ID",
        "descricao": "Pendência",
        "tipo_evidencia": "Evidência exigida",
        "status": "Status",
        "prazo": "Prazo",
        "documento_id": "Documento evidência",
        "criado_em": "Criado em"
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

st.caption("Versão 0.2 - Processos Documentais multiempresa")