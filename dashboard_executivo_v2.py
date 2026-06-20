from pathlib import Path

p = Path("app.py")
txt = p.read_text(encoding="utf-8")

inicio = txt.index("df = carregar_movimentacoes()")

novo = '''
df = carregar_movimentacoes()

recebimentos = df[df["tipo"] == "Receber"]["valor"].sum() if not df.empty else 0
pagamentos = abs(df[df["tipo"] == "Pagar"]["valor"].sum()) if not df.empty else 0
saldo = recebimentos - pagamentos
pendencias = contar_pendencias()

conn = conectar()

try:
    processos_status = pd.read_sql_query("""
        SELECT status, COUNT(*) AS quantidade
        FROM processos_documentais
        WHERE empresa_id = ?
        GROUP BY status
    """, conn, params=(EMPRESA_ID,))
except:
    processos_status = pd.DataFrame(columns=["status", "quantidade"])

try:
    docs_por_tipo = pd.read_sql_query("""
        SELECT tipo_documento, COUNT(*) AS quantidade
        FROM documentos
        WHERE empresa_id = ?
        GROUP BY tipo_documento
    """, conn, params=(EMPRESA_ID,))
except:
    docs_por_tipo = pd.DataFrame(columns=["tipo_documento", "quantidade"])

try:
    financeiro = pd.read_sql_query("""
        SELECT 'Vendido' AS indicador, COALESCE(SUM(valor_total),0) AS valor
        FROM vendas
        WHERE empresa_id = ?
        UNION ALL
        SELECT 'Recebido em banco', COALESCE(SUM(valor),0)
        FROM movimentos_bancarios
        WHERE empresa_id = ? AND tipo = 'Crédito'
        UNION ALL
        SELECT 'Retido', COALESCE(SUM(valor),0)
        FROM documentos
        WHERE empresa_id = ? AND tipo_documento LIKE '%Retenção%'
        UNION ALL
        SELECT 'Pago em compras', COALESCE(SUM(valor_total),0)
        FROM compras
        WHERE empresa_id = ?
    """, conn, params=(EMPRESA_ID, EMPRESA_ID, EMPRESA_ID, EMPRESA_ID))
except:
    financeiro = pd.DataFrame(columns=["indicador", "valor"])

try:
    checklist = pd.read_sql_query("""
        SELECT
            p.titulo AS processo,
            SUM(CASE WHEN d.tipo_documento = 'Nota de Empenho' THEN 1 ELSE 0 END) AS nota_empenho,
            SUM(CASE WHEN d.direcao = 'Nota Fiscal de Compra' THEN 1 ELSE 0 END) AS nf_compra,
            SUM(CASE WHEN d.direcao = 'Nota Fiscal de Venda' THEN 1 ELSE 0 END) AS nf_venda,
            SUM(CASE WHEN d.tipo_documento LIKE '%Comprovante%' THEN 1 ELSE 0 END) AS comprovante,
            SUM(CASE WHEN d.tipo_documento LIKE '%Retenção%' THEN 1 ELSE 0 END) AS retencao,
            p.status
        FROM processos_documentais p
        LEFT JOIN processo_documentos pd ON pd.processo_id = p.id AND pd.empresa_id = p.empresa_id
        LEFT JOIN documentos d ON d.id = pd.documento_id AND d.empresa_id = p.empresa_id
        WHERE p.empresa_id = ?
        GROUP BY p.id
        ORDER BY p.id DESC
    """, conn, params=(EMPRESA_ID,))
except:
    checklist = pd.DataFrame()

conn.close()

st.sidebar.markdown("## GOIA")
st.sidebar.page_link("app.py", label="Dashboard", icon="🏠")
st.sidebar.page_link("pages/1_Importar_Documento.py", label="Importar Documento", icon="📄")
st.sidebar.page_link("pages/2_Contas_a_Receber.py", label="Contas a Receber", icon="💰")
st.sidebar.page_link("pages/3_Contas_a_Pagar.py", label="Contas a Pagar", icon="💸")
st.sidebar.page_link("pages/4_Compras.py", label="Compras", icon="🛒")
st.sidebar.page_link("pages/5_Produtos_Estoque.py", label="Produtos Estoque", icon="📦")
st.sidebar.page_link("pages/6_Vendas.py", label="Vendas", icon="🧾")
st.sidebar.page_link("pages/7_Processos_Documentais.py", label="Processos Documentais", icon="🗂️")
st.sidebar.page_link("pages/8_Conciliacao_Bancaria.py", label="Conciliação Bancária", icon="🏦")

st.title("GOIA Finance Platform")
st.subheader("Dashboard executivo")
st.caption("Visão consolidada de documentos, pendências, financeiro, conciliação e completude dos processos.")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Receita bruta", moeda(recebimentos))

with col2:
    st.metric("Pagamentos", moeda(pagamentos))

with col3:
    st.metric("Margem operacional", moeda(saldo))

with col4:
    st.metric("Pendências abertas", pendencias)

st.divider()

g1, g2 = st.columns(2)

with g1:
    st.subheader("Status dos processos")
    if processos_status.empty:
        st.info("Sem processos.")
    else:
        st.bar_chart(processos_status.set_index("status"))

with g2:
    st.subheader("Documentos recebidos por tipo")
    if docs_por_tipo.empty:
        st.info("Sem documentos.")
    else:
        st.bar_chart(docs_por_tipo.set_index("tipo_documento"))

st.divider()

st.subheader("Resumo financeiro por etapa")

if financeiro.empty:
    st.info("Sem dados financeiros.")
else:
    financeiro_view = financeiro.copy()
    st.bar_chart(financeiro.set_index("indicador"))

    financeiro_view["valor"] = financeiro_view["valor"].apply(moeda)
    st.dataframe(financeiro_view, width="stretch", hide_index=True)

st.divider()

st.subheader("Completude documental por processo")

if checklist.empty:
    st.info("Nenhum processo encontrado.")
else:
    chk = checklist.copy()

    for col in ["nota_empenho", "nf_compra", "nf_venda", "comprovante", "retencao"]:
        chk[col] = chk[col].apply(lambda x: "OK" if int(x or 0) > 0 else "Pendente")

    st.dataframe(chk, width="stretch", hide_index=True)

st.divider()

st.subheader("Movimentações operacionais")

if df.empty:
    st.info("Nenhuma movimentação financeira encontrada.")
else:
    df_view = df.copy()
    df_view["data"] = df_view["data"].apply(data_br)
    df_view["valor"] = df_view["valor"].apply(moeda)
    st.dataframe(df_view, width="stretch", hide_index=True)

st.caption("GOIA Finance Platform · Dashboard de controle financeiro e documental")
'''

p.write_text(txt[:inicio] + novo, encoding="utf-8")
print("OK - dashboard convertido para visão executiva com gráficos e completude documental.")
