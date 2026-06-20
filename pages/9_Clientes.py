
import streamlit as st
import pandas as pd
import sqlite3
import re
import xml.etree.ElementTree as ET
from io import BytesIO

DB_PATH = "bd/gofinance.db"
EMPRESA_ID = 1

st.set_page_config(page_title="Clientes", page_icon="👥", layout="wide")

st.title("👥 Clientes")
st.caption("Cadastro, importação e consulta de clientes.")

def conectar():
    return sqlite3.connect(DB_PATH)

def limpar_doc(valor):
    return re.sub(r"\D", "", valor or "")

def formatar_cnpj(valor):
    n = limpar_doc(valor)
    if len(n) == 14:
        return f"{n[:2]}.{n[2:5]}.{n[5:8]}/{n[8:12]}-{n[12:]}"
    if len(n) == 11:
        return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}"
    return valor or ""

def salvar_cliente(nome, cnpj_cpf, origem):
    if not nome:
        return False, "Informe o nome do cliente."

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    SELECT id FROM clientes
    WHERE empresa_id = ?
      AND (
          cnpj_cpf = ?
          OR nome = ?
      )
    """, (EMPRESA_ID, cnpj_cpf, nome))

    existe = cur.fetchone()

    if existe:
        conn.close()
        return False, "Cliente já cadastrado."

    cur.execute("""
    INSERT INTO clientes (
        empresa_id, nome, cnpj_cpf, origem_cadastro
    )
    VALUES (?, ?, ?, ?)
    """, (EMPRESA_ID, nome, cnpj_cpf, origem))

    conn.commit()
    conn.close()

    return True, "Cliente cadastrado com sucesso."

def extrair_xml_nfe(conteudo):
    root = ET.fromstring(conteudo)

    dest = None
    for elem in root.iter():
        if elem.tag.endswith("dest"):
            dest = elem
            break

    if dest is None:
        return "", ""

    nome = ""
    doc = ""

    for item in dest:
        tag = item.tag.split("}")[-1]
        if tag == "xNome":
            nome = item.text or ""
        if tag in ["CNPJ", "CPF"]:
            doc = item.text or ""

    return nome.strip(), formatar_cnpj(doc)


def valor_apos_rotulo(texto, rotulo):
    linhas = [x.strip() for x in texto.splitlines() if x.strip()]
    for i, linha in enumerate(linhas):
        if linha.upper() == rotulo.upper() and i + 1 < len(linhas):
            return linhas[i + 1].strip()
    return ""

def extrair_pdf(conteudo):
    texto = ""
    try:
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(conteudo))
        for page in reader.pages:
            texto += page.extract_text() or ""
            texto += "\n"
    except Exception:
        texto = ""

    nome = valor_apos_rotulo(texto, "NOME EMPRESARIAL")
    fantasia = valor_apos_rotulo(texto, "TÍTULO DO ESTABELECIMENTO (NOME DE FANTASIA)")
    cep = valor_apos_rotulo(texto, "CEP")
    municipio = valor_apos_rotulo(texto, "MUNICÍPIO")
    uf = valor_apos_rotulo(texto, "UF")
    telefone = valor_apos_rotulo(texto, "TELEFONE")
    situacao = valor_apos_rotulo(texto, "SITUAÇÃO CADASTRAL")

    cnpj = ""
    m = re.search(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}", texto)
    if m:
        cnpj = formatar_cnpj(m.group())

    if not nome:
        nome = fantasia

    return {
        "nome": nome,
        "cnpj_cpf": cnpj,
        "fantasia": fantasia,
        "cep": cep,
        "municipio": municipio,
        "uf": uf,
        "telefone": telefone,
        "situacao": situacao,
        "texto": texto,
    }

aba1, aba2, aba3 = st.tabs([
    "Clientes cadastrados",
    "Cadastrar manualmente",
    "Importar documento"
])

with aba1:
    st.subheader("Clientes cadastrados")

    conn = conectar()
    clientes = pd.read_sql_query("""
    SELECT
        id,
        nome,
        cnpj_cpf,
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
        clientes = clientes[
            clientes["nome"].fillna("").str.contains(busca, case=False, na=False)
            | clientes["cnpj_cpf"].fillna("").str.contains(busca, case=False, na=False)
        ]

    if clientes.empty:
        st.info("Nenhum cliente cadastrado.")
    else:
        st.dataframe(clientes.drop(columns=["id"]), width="stretch", hide_index=True)

        with st.expander("Ver histórico financeiro do cliente"):
            cliente_nome = st.selectbox("Selecionar cliente", clientes["nome"].tolist())
            cliente_id = int(clientes[clientes["nome"] == cliente_nome]["id"].iloc[0])

            conn = conectar()

            notas = pd.read_sql_query("""
            SELECT numero_nfe, serie_nfe, data_emissao, valor, status_processamento
            FROM documentos
            WHERE empresa_id = ?
              AND direcao = 'Nota Fiscal de Venda'
              AND (
                  cnpj_destinatario = (SELECT cnpj_cpf FROM clientes WHERE id = ?)
                  OR nome_destinatario = (SELECT nome FROM clientes WHERE id = ?)
              )
            ORDER BY data_emissao DESC
            """, conn, params=(EMPRESA_ID, cliente_id, cliente_id))

            receber = pd.read_sql_query("""
            SELECT descricao, valor, valor_baixado, data_vencimento, data_baixa, status
            FROM contas_receber
            WHERE empresa_id = ?
              AND cliente_id = ?
            ORDER BY data_vencimento DESC
            """, conn, params=(EMPRESA_ID, cliente_id))

            conn.close()

            st.markdown("### Notas fiscais emitidas")
            st.dataframe(notas, width="stretch", hide_index=True)

            st.markdown("### Contas a receber")
            st.dataframe(receber, width="stretch", hide_index=True)

with aba2:
    st.subheader("Cadastro manual")

    with st.form("form_cliente"):
        nome = st.text_input("Nome / Razão Social")
        cnpj_cpf = st.text_input("CNPJ / CPF")
        salvar = st.form_submit_button("Salvar cliente")

    if salvar:
        ok, msg = salvar_cliente(nome.strip(), formatar_cnpj(cnpj_cpf), "Manual")
        st.success(msg) if ok else st.warning(msg)

with aba3:
    st.subheader("Importar documento para cadastrar cliente")

    st.write("Use esta opção para cadastrar cliente a partir de NF-e de saída, XML, PDF ou CSV.")

    arquivo = st.file_uploader(
        "Enviar documento do cliente",
        type=["xml", "pdf", "csv", "txt"]
    )

    if arquivo:
        conteudo = arquivo.read()
        nome_sugerido = ""
        cnpj_sugerido = ""

        if arquivo.name.lower().endswith(".xml"):
            nome_sugerido, cnpj_sugerido = extrair_xml_nfe(conteudo)

        elif arquivo.name.lower().endswith(".pdf"):
            dados_pdf = extrair_pdf(conteudo)
            nome_sugerido = dados_pdf.get("nome", "")
            cnpj_sugerido = dados_pdf.get("cnpj_cpf", "")
            st.write("Dados extraídos do PDF:")
            st.json({
                "nome": dados_pdf.get("nome", ""),
                "cnpj_cpf": dados_pdf.get("cnpj_cpf", ""),
                "fantasia": dados_pdf.get("fantasia", ""),
                "cep": dados_pdf.get("cep", ""),
                "municipio": dados_pdf.get("municipio", ""),
                "uf": dados_pdf.get("uf", ""),
                "telefone": dados_pdf.get("telefone", ""),
                "situacao": dados_pdf.get("situacao", ""),
            })

        elif arquivo.name.lower().endswith(".csv"):
            df = pd.read_csv(BytesIO(conteudo))
            st.dataframe(df, width="stretch", hide_index=True)
            st.info("Para CSV, use colunas nome e cnpj_cpf.")
            if "nome" in df.columns:
                nome_sugerido = str(df.iloc[0]["nome"])
            if "cnpj_cpf" in df.columns:
                cnpj_sugerido = formatar_cnpj(str(df.iloc[0]["cnpj_cpf"]))

        st.markdown("### Dados identificados")

        with st.form("form_cliente_documento"):
            nome_doc = st.text_input("Nome / Razão Social identificado", value=nome_sugerido)
            cnpj_doc = st.text_input("CNPJ / CPF identificado", value=cnpj_sugerido)
            confirmar = st.form_submit_button("Cadastrar cliente a partir do documento")

        if confirmar:
            ok, msg = salvar_cliente(nome_doc.strip(), formatar_cnpj(cnpj_doc), f"Documento: {arquivo.name}")
            st.success(msg) if ok else st.warning(msg)