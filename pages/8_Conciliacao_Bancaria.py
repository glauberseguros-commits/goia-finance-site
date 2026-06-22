import streamlit as st
from utils.ui import aplicar_estilo_premium
from utils.premium import aplicar_premium_goia, hero
import pandas as pd
import sqlite3
from utils.formatadores import formatar_moeda, formatar_data
from utils.auth import empresa_logada, exigir_login

DB_PATH = "bd/gofinance.db"

exigir_login()
EMPRESA_ID_ATIVA = empresa_logada()

st.set_page_config(
    page_title="Conciliação Bancária",
    page_icon="🔄",
    layout="wide"
)

aplicar_estilo_premium()
aplicar_premium_goia()

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

hero(
    "Conciliacao Bancaria",
    "Relacione automaticamente movimentacoes bancarias com contas a receber, contas a pagar e baixas financeiras.",
    icone="GOIA"
)


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
        LEFT JOIN clientes c
            ON c.id = cr.cliente_id
           AND c.empresa_id = cr.empresa_id
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
        LEFT JOIN fornecedores f
            ON f.id = cp.fornecedor_id
           AND f.empresa_id = cp.empresa_id
        WHERE cp.empresa_id = ?
          AND cp.status = 'Pendente'
        ORDER BY cp.data_vencimento ASC, cp.id ASC
    """, conn, params=(EMPRESA_ID_ATIVA,))

    conn.close()
    return df


def gerar_sugestoes(df_mov, df_rec, df_pag):
    sugestoes = []

    if df_mov.empty:
        return pd.DataFrame(sugestoes)

    for _, mov in df_mov[df_mov["conciliado"].fillna(0).astype(int) == 0].iterrows():
        tipo_movimento = str(mov["tipo"] or "").strip()

        if tipo_movimento == "Crédito":
            candidatos = df_rec.copy()
            tipo_conta = "Receber"
        else:
            candidatos = df_pag.copy()
            tipo_conta = "Pagar"

        if candidatos.empty:
            continue

        candidatos["valor"] = pd.to_numeric(candidatos["valor"], errors="coerce").fillna(0)
        valor_movimento = abs(float(mov["valor"] or 0))

        candidatos["diferenca"] = (candidatos["valor"] - valor_movimento).abs()
        melhor = candidatos.sort_values("diferenca").iloc[0]

        diferenca = float(melhor["diferenca"])
        score = 100 if diferenca < 0.01 else max(0, 80 - diferenca)

        sugestoes.append({
            "movimento_id": int(mov["id"]),
            "data_movimento": mov["data_movimento"],
            "historico": mov["historico"],
            "tipo_movimento": tipo_movimento,
            "valor_movimento": float(mov["valor"] or 0),
            "tipo_conta": tipo_conta,
            "conta_id": int(melhor["id"]),
            "contraparte": melhor["contraparte"],
            "descricao": melhor["descricao"],
            "valor_conta": float(melhor["valor"]),
            "diferenca": diferenca,
            "score": float(score)
        })

    return pd.DataFrame(sugestoes)


def obter_processo_por_documento(cursor, documento_id):
    if not documento_id:
        return None

    cursor.execute("""
        SELECT processo_id
        FROM processo_documentos
        WHERE documento_id = ?
          AND empresa_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (documento_id, EMPRESA_ID_ATIVA))

    row = cursor.fetchone()
    return row[0] if row else None


def atualizar_pendencia_processo(cursor, processo_id, tipo_conta, movimento_id):
    if not processo_id:
        return

    if tipo_conta == "Receber":
        tipos_alvo = ["Extrato bancário", "Recebimento bancário", "Comprovante de recebimento"]
        descricao_evidencia = "Recebimento conciliado com movimento bancário"
        tipo_evidencia = "Recebimento bancário"
    else:
        tipos_alvo = ["Extrato bancário", "Comprovante de pagamento"]
        descricao_evidencia = "Pagamento conciliado com movimento bancário"
        tipo_evidencia = "Pagamento bancário"

    for tipo in tipos_alvo:
        cursor.execute("""
            UPDATE processo_pendencias
            SET status = 'Concluída',
                documento_id = ?
            WHERE processo_id = ?
              AND empresa_id = ?
              AND status = 'Pendente'
              AND tipo_evidencia = ?
        """, (
            movimento_id,
            processo_id,
            EMPRESA_ID_ATIVA,
            tipo
        ))

    cursor.execute("""
        INSERT INTO processo_evidencias (
            empresa_id,
            processo_id,
            documento_id,
            tipo_evidencia,
            descricao,
            valor,
            data_evidencia,
            origem,
            status
        )
        SELECT
            empresa_id,
            ?,
            documento_comprovante_id,
            ?,
            ?,
            ABS(valor),
            data_movimento,
            'Conciliação bancária',
            'Validada'
        FROM movimentos_bancarios
        WHERE id = ?
          AND empresa_id = ?
    """, (
        processo_id,
        tipo_evidencia,
        descricao_evidencia,
        movimento_id,
        EMPRESA_ID_ATIVA
    ))

    cursor.execute("""
        SELECT COUNT(*)
        FROM processo_pendencias
        WHERE processo_id = ?
          AND empresa_id = ?
          AND status = 'Pendente'
    """, (processo_id, EMPRESA_ID_ATIVA))

    pendentes = cursor.fetchone()[0]

    if pendentes == 0:
        cursor.execute("""
            UPDATE processos_documentais
            SET status = 'Concluído',
                proxima_acao = 'Processo sem pendências abertas'
            WHERE id = ?
              AND empresa_id = ?
        """, (processo_id, EMPRESA_ID_ATIVA))
    else:
        cursor.execute("""
            UPDATE processos_documentais
            SET status = 'Aberto',
                proxima_acao = 'Aguardando evidências pendentes'
            WHERE id = ?
              AND empresa_id = ?
        """, (processo_id, EMPRESA_ID_ATIVA))


def conciliar(movimento_id, tipo_conta, conta_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT conciliado, valor, data_movimento
            FROM movimentos_bancarios
            WHERE id = ?
              AND empresa_id = ?
        """, (movimento_id, EMPRESA_ID_ATIVA))

        mov = cur.fetchone()

        if not mov:
            raise ValueError("Movimento bancário não encontrado.")

        if int(mov[0] or 0) == 1:
            raise ValueError("Este movimento já está conciliado.")

        valor_movimento = abs(float(mov[1] or 0))
        data_movimento = mov[2]

        if tipo_conta == "Pagar":
            cur.execute("""
                SELECT documento_id, valor
                FROM contas_pagar
                WHERE id = ?
                  AND empresa_id = ?
                  AND status = 'Pendente'
            """, (conta_id, EMPRESA_ID_ATIVA))

            conta = cur.fetchone()

            if not conta:
                raise ValueError("Conta a pagar pendente não encontrada.")

            documento_id = conta[0]
            conta_pagar_id = conta_id
            conta_receber_id = None
            tipo_conciliacao = "Pagamento"

            cur.execute("""
                UPDATE contas_pagar
                SET status = 'Baixada',
                    data_baixa = ?,
                    valor_baixado = ?,
                    observacao_baixa = 'Baixa por conciliação bancária'
                WHERE id = ?
                  AND empresa_id = ?
            """, (
                data_movimento,
                valor_movimento,
                conta_id,
                EMPRESA_ID_ATIVA
            ))

        else:
            cur.execute("""
                SELECT documento_id, valor
                FROM contas_receber
                WHERE id = ?
                  AND empresa_id = ?
                  AND status = 'Pendente'
            """, (conta_id, EMPRESA_ID_ATIVA))

            conta = cur.fetchone()

            if not conta:
                raise ValueError("Conta a receber pendente não encontrada.")

            documento_id = conta[0]
            conta_pagar_id = None
            conta_receber_id = conta_id
            tipo_conciliacao = "Recebimento"

            cur.execute("""
                UPDATE contas_receber
                SET status = 'Baixada',
                    data_baixa = ?,
                    valor_baixado = ?,
                    observacao_baixa = 'Baixa por conciliação bancária'
                WHERE id = ?
                  AND empresa_id = ?
            """, (
                data_movimento,
                valor_movimento,
                conta_id,
                EMPRESA_ID_ATIVA
            ))

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

        processo_id = obter_processo_por_documento(cur, documento_id)
        atualizar_pendencia_processo(cur, processo_id, tipo_conta, movimento_id)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


df_mov = carregar_movimentos()
df_rec = carregar_receber_pendentes()
df_pag = carregar_pagar_pendentes()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Movimentos", len(df_mov))

with col2:
    st.metric(
        "Não conciliados",
        len(df_mov[df_mov["conciliado"].fillna(0).astype(int) == 0]) if not df_mov.empty else 0
    )

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

    df_show["data_movimento"] = df_show["data_movimento"].fillna("").apply(formatar_data)
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
        try:
            conciliar(
                int(linha["movimento_id"]),
                linha["tipo_conta"],
                int(linha["conta_id"])
            )
            st.success("Movimento conciliado, conta baixada e processo documental atualizado.")
            st.rerun()
        except Exception as e:
            st.error(str(e))

st.divider()

st.subheader("Movimentos bancários")

if df_mov.empty:
    st.warning("Nenhum movimento bancário cadastrado.")
else:
    df_mov_show = df_mov.copy()
    df_mov_show["data_movimento"] = df_mov_show["data_movimento"].fillna("").apply(formatar_data)
    df_mov_show["valor"] = df_mov_show["valor"].apply(formatar_moeda)
    df_mov_show["conciliado"] = df_mov_show["conciliado"].fillna(0).astype(int).apply(lambda x: "Sim" if x == 1 else "Não")

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

st.caption("Versão 0.2 - Conciliação Bancária multiempresa")