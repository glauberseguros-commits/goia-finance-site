from pathlib import Path

p = Path("app.py")

novo = r'''
import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path

DB_PATH = "bd/gofinance.db"
EMPRESA_ID = 1

st.set_page_config(
    page_title="GOIA Finance Platform",
    page_icon="💰",
    layout="wide"
)

st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none; }

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.metric-card {
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 22px;
    background: #ffffff;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}

.metric-label {
    color: #64748b;
    font-size: 0.88rem;
    margin-bottom: 8px;
}

.metric-value {
    color: #0f172a;
    font-size: 1.55rem;
    font-weight: 800;
}

.metric-sub {
    color: #94a3b8;
    font-size: 0.78rem;
    margin-top: 6px;
}

.hero {
    border-radius: 24px;
    padding: 34px;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 55%, #334155 100%);
    color: white;
    margin-bottom: 26px;
}

.hero h1 {
    font-size: 2.25rem;
    margin-bottom: 8px;
}

.hero p {
    color: #cbd5e1;
    font-size: 1.02rem;
    max-width: 980px;
}

.card-link {
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 22px;
    background: #ffffff;
    min-height: 180px;
}

.status-ok {
    background: #dcfce7;
    color: #166534;
    padding: 5px 10px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.8rem;
}
</style>
""", unsafe_allow_html=True)

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

def scalar(sql, default=0):
    conn = conectar()
    try:
        cur = conn.cursor()
        cur.execute(sql, (EMPRESA_ID,))
        r = cur.fetchone()
        return r[0] if r and r[0] is not None else default
    except:
        return default
    finally:
        conn.close()

def query(sql):
    conn = conectar()
    try:
        return pd.read_sql_query(sql, conn, params=(EMPRESA_ID,))
    except:
        return pd.DataFrame()
    finally:
        conn.close()

receita_bruta = scalar("SELECT COALESCE(SUM(valor_total),0) FROM vendas WHERE empresa_id = ?")
compras_total = scalar("SELECT COALESCE(SUM(valor_total),0) FROM compras WHERE empresa_id = ?")
recebido_banco = scalar("SELECT COALESCE(SUM(valor),0) FROM movimentos_bancarios WHERE empresa_id = ? AND tipo = 'Crédito'")
retencoes = scalar("SELECT COALESCE(SUM(valor),0) FROM documentos WHERE empresa_id = ? AND tipo_documento LIKE '%Retenção%'")
margem_bruta = receita_bruta - compras_total
pendencias = scalar("SELECT COUNT(*) FROM processo_pendencias WHERE empresa_id = ? AND status = 'Pendente'")
processos_concluidos = scalar("SELECT COUNT(*) FROM processos_documentais WHERE empresa_id = ? AND status = 'Concluído'")
conciliacoes = scalar("SELECT COUNT(*) FROM conciliacoes WHERE empresa_id = ? AND status = 'Conciliado'")

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

st.markdown("""
<div class="hero">
    <h1>GOIA Finance Platform</h1>
    <p>Automação financeira document-driven: cada documento gera evidências, pendências, vínculos operacionais, baixa, conciliação e encerramento do processo.</p>
</div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

cards = [
    ("Receita bruta", moeda(receita_bruta), "Notas fiscais de venda"),
    ("Caixa recebido", moeda(recebido_banco), "Créditos bancários conciliáveis"),
    ("Retenções", moeda(retencoes), "Diferença justificada entre NF e banco"),
    ("Margem bruta", moeda(margem_bruta), "Receita menos custo de compra"),
]

for col, (label, value, sub) in zip([c1, c2, c3, c4], cards):
    with col:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>
        ''', unsafe_allow_html=True)

c5, c6, c7, c8 = st.columns(4)

cards2 = [
    ("Compras", moeda(compras_total), "Custo operacional vinculado"),
    ("Processos concluídos", processos_concluidos, "Fluxos encerrados"),
    ("Conciliações", conciliacoes, "Matches bancários validados"),
    ("Pendências abertas", pendencias, "Ações que bloqueiam fechamento"),
]

for col, (label, value, sub) in zip([c5, c6, c7, c8], cards2):
    with col:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>
        ''', unsafe_allow_html=True)

st.divider()

st.subheader("Fluxo operacional")
m1, m2, m3 = st.columns(3)

with m1:
    with st.container(border=True):
        st.markdown("### 📄 Importar Documento")
        st.write("Entrada única para notas, comprovantes, boletos, extratos, XML, imagens e planilhas.")
        st.page_link("pages/1_Importar_Documento.py", label="Acessar importação")

with m2:
    with st.container(border=True):
        st.markdown("### 🗂️ Processos Documentais")
        st.write("Agrupa documentos, evidências, pendências, compras, vendas e baixas por processo.")
        st.page_link("pages/7_Processos_Documentais.py", label="Acessar processos")

with m3:
    with st.container(border=True):
        st.markdown("### 🏦 Conciliação Bancária")
        st.write("Valida recebimentos e pagamentos contra contas, comprovantes, retenções e extratos.")
        st.page_link("pages/8_Conciliacao_Bancaria.py", label="Acessar conciliação")

st.divider()

st.subheader("Últimos processos documentais")

processos = query("""
SELECT
    titulo,
    tipo_operacao,
    contraparte_nome,
    valor_total,
    valor_recebido,
    valor_retido,
    margem_bruta,
    status,
    proxima_acao,
    criado_em
FROM processos_documentais
WHERE empresa_id = ?
ORDER BY id DESC
LIMIT 10
""")

if processos.empty:
    st.info("Nenhum processo documental encontrado.")
else:
    processos["valor_total"] = processos["valor_total"].apply(moeda)
    processos["valor_recebido"] = processos["valor_recebido"].apply(moeda)
    processos["valor_retido"] = processos["valor_retido"].apply(moeda)
    processos["margem_bruta"] = processos["margem_bruta"].apply(moeda)
    processos["criado_em"] = processos["criado_em"].apply(data_br)
    st.dataframe(processos, width="stretch", hide_index=True)

st.subheader("Movimentações operacionais")

mov = query("""
SELECT data_vencimento AS data, 'Receber' AS tipo, descricao, categoria, valor, status
FROM contas_receber
WHERE empresa_id = ?
UNION ALL
SELECT data_vencimento AS data, 'Pagar' AS tipo, descricao, categoria, -valor AS valor, status
FROM contas_pagar
WHERE empresa_id = ?
ORDER BY data DESC
""")

if mov.empty:
    st.info("Nenhuma movimentação operacional encontrada.")
else:
    mov["data"] = mov["data"].apply(data_br)
    mov["valor"] = mov["valor"].apply(moeda)
    st.dataframe(mov, width="stretch", hide_index=True)

st.caption("GOIA Finance Platform · Documentos → Evidências → Pendências → Operação → Conciliação → Encerramento")
'''

p.write_text(novo, encoding="utf-8")
print("OK - Dashboard premium reconstruído com base operacional.")
