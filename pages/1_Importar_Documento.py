import streamlit as st
import re
import sqlite3
import pytesseract
from pdf2image import convert_from_bytes
from pypdf import PdfReader
from datetime import datetime

DB_PATH = "bd/gofinance.db"

from utils.auth import empresa_logada, exigir_login

exigir_login()
EMPRESA_ID_ATIVA = empresa_logada()

st.set_page_config(
    page_title="Importar Documento",
    page_icon="📄",
    layout="wide"
)


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
    st.sidebar.page_link("pages/7_Processos_Documentais.py", label="Processos Documentais", icon="🗂️")
    st.sidebar.page_link("pages/8_Conciliacao_Bancaria.py", label="Conciliação Bancária", icon="🏦")

menu_goia()



st.title("📄 Importar Documento Financeiro")
st.caption("Triagem ERP: compra, venda, despesa, comprovante, extrato e cadastro.")

arquivos = st.file_uploader(
    "Selecione um ou mais documentos PDF",
    type=["pdf"],
    accept_multiple_files=True
)

arquivo = None

if arquivos:
    if len(arquivos) == 1:
        arquivo = arquivos[0]
    else:
        nomes_arquivos = [a.name for a in arquivos]
        nome_escolhido = st.selectbox(
            "Escolha qual documento deseja processar agora",
            nomes_arquivos
        )
        arquivo = next(a for a in arquivos if a.name == nome_escolhido)

        st.info(
            f"{len(arquivos)} documentos selecionados. "
            "Escolha um documento por vez para revisar a classificação antes de gravar no ERP."
        )


# =========================
# UTILITÁRIOS
# =========================

def conectar():
    return sqlite3.connect(DB_PATH)

def obter_cnpj_empresa_logada():
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT cnpj
            FROM empresas
            WHERE id = ?
        """, (EMPRESA_ID_ATIVA,))
        row = cur.fetchone()
    except Exception:
        row = None

    conn.close()

    if row and row[0]:
        return normalizar_cnpj(row[0])

    return ""

CNPJ_EMPRESA = obter_cnpj_empresa_logada()

def normalizar_cnpj(cnpj):
    numeros = re.sub(r"\D", "", cnpj or "")
    if len(numeros) != 14:
        return cnpj or ""
    return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"

def encontrar_cnpjs(texto):
    from utils.validadores import validar_cnpj

    encontrados = re.findall(
        r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}",
        texto or ""
    )

    validos = []

    for cnpj in encontrados:
        if validar_cnpj(cnpj):
            validos.append(
                normalizar_cnpj(cnpj)
            )

    return list(dict.fromkeys(validos))

def encontrar_datas(texto):
    datas = re.findall(r"\b\d{2}/\d{2}/\d{4}\b", texto or "")
    return list(dict.fromkeys(datas))

def converter_data(data_br):
    if not data_br:
        return None
    try:
        return datetime.strptime(data_br, "%d/%m/%Y").strftime("%Y-%m-%d")
    except:
        return None

def encontrar_valores(texto):
    valores = re.findall(r"\d{1,3}(?:\.\d{3})*,\d{2}", texto or "")
    return list(dict.fromkeys(valores))

def converter_valor(valor):
    if not valor:
        return 0.0
    valor = str(valor).replace("R$", "").replace(" ", "")
    valor = valor.replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except:
        return 0.0

def maior_valor(texto):
    valores = [converter_valor(v) for v in encontrar_valores(texto)]
    valores = [v for v in valores if v > 0]
    return max(valores) if valores else 0.0

def extrair_chave_acesso_nfe(texto):
    t = texto or ""
    grupos = re.findall(r"(?:\d{4}\s*){11}", t)

    for grupo in grupos:
        chave = re.sub(r"\D", "", grupo)
        if len(chave) == 44:
            return chave

    return ""


def formatar_chave_acesso(chave):
    chave = re.sub(r"\D", "", chave or "")
    if len(chave) != 44:
        return chave
    return " ".join(chave[i:i+4] for i in range(0, 44, 4))


def extrair_numero_serie_nfe(texto, chave_acesso=""):
    chave = re.sub(r"\D", "", chave_acesso or "")
    numero = ""
    serie = ""

    if len(chave) == 44:
        serie = chave[22:25].lstrip("0") or "0"
        numero = chave[25:34].lstrip("0") or "0"

    return numero, serie

def extrair_texto_pypdf(arquivo):
    arquivo.seek(0)
    reader = PdfReader(arquivo)
    texto = ""
    for page in reader.pages:
        texto += page.extract_text() or ""
    return texto.strip()

def extrair_texto_ocr(arquivo):
    arquivo.seek(0)
    imagens = convert_from_bytes(arquivo.read(), dpi=300)
    texto = ""
    for imagem in imagens:
        texto += pytesseract.image_to_string(imagem, lang="por+eng")
    return texto.strip()

def extrair_texto_pdf(arquivo):
    texto = extrair_texto_pypdf(arquivo)
    if len(texto) < 50:
        st.warning("PDF com pouco texto detectado. Aplicando OCR...")
        texto = extrair_texto_ocr(arquivo)
    return texto

# =========================
# CLASSIFICAÇÃO
# =========================

def classificar_tipo_documento(texto):
    t = (texto or "").upper()

    # Regra central:
    # O tipo do documento principal tem prioridade sobre referências internas.
    # Uma NF-e pode citar nota de empenho, processo, licitação ou contrato nas informações complementares.
    if (
        "DANFE" in t
        or "NF-E" in t
        or "NFE" in t
        or "NOTA FISCAL" in t
        or "NOTA FISCAL ELETRONICA" in t
        or "NOTA FISCAL ELETRÔNICA" in t
        or "CHAVE DE ACESSO" in t
        or "DOCUMENTO AUXILIAR DA NOTA FISCAL" in t
    ):
        return "Nota Fiscal"

    if "FICHA DE COMPENSAÇÃO" in t or "BOLETO" in t or "PAGAR PREFERENCIALMENTE" in t or "PAGÁVEL PREFERENCIALMENTE" in t:
        return "Boleto / Despesa"

    if "COMPROVANTE" in t and ("PIX" in t or "TRANSFERÊNCIA" in t or "TRANSFERENCIA" in t or "PAGAMENTO" in t or "RECEBIMENTO" in t):
        if "RECEBEMOS" in t or "RECEBIMENTO" in t:
            return "Comprovante de Recebimento"
        return "Comprovante de Pagamento"

    if "EXTRATO" in t and ("SALDO" in t or "LANÇAMENTO" in t or "LANCAMENTO" in t):
        return "Extrato Bancário"

    if "CADASTRO NACIONAL DA PESSOA JURÍDICA" in t:
        return "Cartão CNPJ"

    if (
        "NOTA DE EMPENHO" in t
        or " EMPENHO " in t
        or "NE00" in t
    ):
        return "Nota de Empenho"

    return "A classificar"


def sugerir_direcao_nf(texto):
    t = (texto or "").upper()

    if "COMANDO DA MARINHA" in t:
        return "Nota Fiscal de Venda"

    if "DESTINATÁRIO" in t and CNPJ_EMPRESA in texto:
        return "Nota Fiscal de Compra"

    return "Nota Fiscal de Compra"

def identificar_nome_por_cnpj(texto, cnpj):
    if not cnpj:
        return ""

    linhas = [l.strip() for l in (texto or "").splitlines() if l.strip()]
    for i, linha in enumerate(linhas):
        if cnpj in linha or re.sub(r"\D", "", cnpj) in re.sub(r"\D", "", linha):
            candidatos = []
            if i > 0:
                candidatos.append(linhas[i - 1])
            if i > 1:
                candidatos.append(linhas[i - 2])
            if i + 1 < len(linhas):
                candidatos.append(linhas[i + 1])

            for c in candidatos:
                c_up = c.upper()
                if len(c) >= 5 and not re.search(r"\d{2}/\d{2}/\d{4}", c) and "CNPJ" not in c_up:
                    return c[:120]
    return ""

def extrair_valor_total_nfe(texto):
    t = texto or ""
    linhas = [l.strip() for l in t.splitlines() if l.strip()]
    texto_up = t.upper()

    # 1) Caso OCR da DANFE traga o rótulo quebrado: V. TOTAL DE PRODUTOS / V. TOTAL DA NOTA
    rotulos_prioritarios = [
        "V. TOTAL DA NOTA",
        "VALOR TOTAL DA NOTA",
        "V TOTAL DA NOTA",
        "VALOR TOTAL DOS PRODUTOS",
        "V. TOTAL DE PRODUTOS",
        "V TOTAL DE PRODUTOS",
        "TOTAL DE PRODUTOS"
    ]

    for i, linha in enumerate(linhas):
        linha_up = linha.upper()

        if any(rotulo in linha_up for rotulo in rotulos_prioritarios):
            janela = " ".join(linhas[i:i+8])
            valores = encontrar_valores(janela)
            valores_validos = []

            for v in valores:
                valor = converter_valor(v)
                # Evita zeros de impostos e evita valores absurdos de CNPJ/chave.
                if 0 < valor < 100000000:
                    valores_validos.append(valor)

            if valores_validos:
                return max(valores_validos)

    # 2) Caso apareça "V. TOTAL DA NOTA 2.598,65" na mesma linha
    padroes = [
        r"V\.\s*TOTAL\s*DA\s*NOTA\s*(?:R\$)?\s*([\d\.\,]+)",
        r"VALOR\s*TOTAL\s*DA\s*NOTA\s*(?:R\$)?\s*([\d\.\,]+)",
        r"V\.\s*TOTAL\s*DE\s*PRODUTOS\s*(?:R\$)?\s*([\d\.\,]+)",
        r"VALOR\s*TOTAL\s*DOS\s*PRODUTOS\s*(?:R\$)?\s*([\d\.\,]+)",
        r"VALOR\s*A\s*PAGAR\s*(?:R\$)?\s*([\d\.\,]+)",
        r"TOTAL\s*GERAL\s*(?:R\$)?\s*([\d\.\,]+)"
    ]

    for padrao in padroes:
        m = re.search(padrao, t, flags=re.IGNORECASE)
        if m:
            valor = converter_valor(m.group(1))
            if valor > 0:
                return valor

    # 3) Fallback específico para itens da NF-e.
    # Procura linhas de produto/serviço e captura valores monetários nelas.
    palavras_item = [
        "MAQUINA",
        "MÁQUINA",
        "PRODUTO",
        "SERVICO",
        "SERVIÇO",
        "MATRIZ",
        "CHAVE",
        "UN[",
        "UN "
    ]

    candidatos_item = []

    for linha in linhas:
        linha_up = linha.upper()

        if any(p in linha_up for p in palavras_item):
            valores_linha = encontrar_valores(linha)

            for v in valores_linha:
                valor = converter_valor(v)

                if valor <= 0:
                    continue

                # Evita CNPJ OCRizado, chave de acesso, protocolo e valores absurdos.
                if valor >= 100000:
                    continue

                candidatos_item.append(valor)

    if candidatos_item:
        return max(candidatos_item)

    # Para NF-e, se não encontrou rótulo nem item, não inventa valor.
    return 0.0

def extrair_emitente_destinatario_nfe(texto):
    linhas = [l.strip() for l in (texto or "").splitlines() if l.strip()]
    t = texto or ""
    t_up = t.upper()
    cnpjs = encontrar_cnpjs(texto)

    emitente_nome = ""
    emitente_cnpj = ""
    destinatario_nome = ""
    destinatario_cnpj = ""

    # Emitente conhecido: própria empresa GODS.
    if (
        "GODS PRODUTOS" in t_up
        or "GO LICITAÇÕES" in t_up
        or "GO LICITACOES" in t_up
        or CNPJ_EMPRESA in cnpjs
    ):
        emitente_nome = "GODS PRODUTOS SERVICOS & EVENTOS LTDA"
        emitente_cnpj = CNPJ_EMPRESA

    # Emitente conhecido: fornecedor Ponto Certo.
    if "PONTO CERTO" in t_up:
        emitente_nome = "PONTO CERTO COMERCIO DE FERRAGENS LTDA"
        emitente_cnpj = "11.877.694/0001-66"

    # Destinatário conhecido: Marinha.
    if "COMANDO DA MARINHA" in t_up:
        destinatario_nome = "COMANDO DA MARINHA"
        for c in cnpjs:
            if c != CNPJ_EMPRESA:
                destinatario_cnpj = c
                break

    # Bloco destinatário/remetente.
    for i, linha in enumerate(linhas):
        linha_up = linha.upper()

        if "DESTINATÁRIO" in linha_up or "DESTINATARIO" in linha_up or "REMETENTE" in linha_up:
            trecho = " ".join(linhas[i:i+12])
            trecho_up = trecho.upper()
            cnpjs_trecho = encontrar_cnpjs(trecho)

            if "COMANDO DA MARINHA" in trecho_up:
                destinatario_nome = "COMANDO DA MARINHA"

            for c in cnpjs_trecho:
                if c != CNPJ_EMPRESA:
                    destinatario_cnpj = c
                    nome = identificar_nome_por_cnpj(trecho, c)
                    if nome and "CHAVE DE ACESSO" not in nome.upper():
                        destinatario_nome = nome
                    break

            if CNPJ_EMPRESA in cnpjs_trecho and not destinatario_cnpj:
                destinatario_cnpj = CNPJ_EMPRESA
                destinatario_nome = "GODS PRODUTOS SERVICOS & EVENTOS LTDA"

    # Se a empresa própria não for emitente, mas aparece como destinatária, corrigir compra.
    if emitente_cnpj == CNPJ_EMPRESA and destinatario_cnpj == CNPJ_EMPRESA:
        destinatario_cnpj = ""
        destinatario_nome = ""

    # Fallback: se ainda não tem destinatário e há CNPJ diferente da empresa.
    if not destinatario_cnpj:
        for c in cnpjs:
            if c != CNPJ_EMPRESA:
                destinatario_cnpj = c
                nome = identificar_nome_por_cnpj(texto, c)
                if nome and "CHAVE DE ACESSO" not in nome.upper():
                    destinatario_nome = nome
                break

    # Se não achou emitente e há CNPJ diferente da empresa, assumir fornecedor externo.
    if not emitente_cnpj:
        for c in cnpjs:
            if c != CNPJ_EMPRESA:
                emitente_cnpj = c
                nome = identificar_nome_por_cnpj(texto, c)
                emitente_nome = nome or ""
                break

    return {
        "emitente_nome": emitente_nome,
        "emitente_cnpj": emitente_cnpj,
        "destinatario_nome": destinatario_nome,
        "destinatario_cnpj": destinatario_cnpj
    }



def extrair_descricao_produto_nfe(texto):
    linhas = [l.strip() for l in (texto or "").splitlines() if l.strip()]

    for linha in linhas:
        linha_up = linha.upper()

        if "MAQUINA" in linha_up or "MÁQUINA" in linha_up:
            partes = linha.split("|")

            for parte in partes:
                p = parte.strip()

                if "MAQUINA" in p.upper() or "MÁQUINA" in p.upper():
                    p = p.replace("[", " ").replace("]", " ")
                    p = " ".join(p.split())
                    return p[:180]

            return " ".join(linha.split())[:180]

    return ""

def analisar_documento(texto):
    cnpjs = encontrar_cnpjs(texto)
    datas = encontrar_datas(texto)

    tipo_detectado = classificar_tipo_documento(texto)

    if tipo_detectado == "Nota de Empenho":

        nome_orgao = "Órgão Público"

        texto_up = (texto or "").upper()

        if "ESTADO-MAIOR DA ARMADA" in texto_up:
            nome_orgao = "ESTADO-MAIOR DA ARMADA"

        elif "COMANDO DA MARINHA" in texto_up:
            nome_orgao = "COMANDO DA MARINHA"

        return {
            "tipo_detectado": "Nota de Empenho",
            "direcao_sugerida": "Nota de Empenho",
            "cnpjs": [],
            "parte_cnpj": "",
            "parte_nome": nome_orgao,
            "valor": maior_valor(texto),
            "data_emissao": None,
            "data_vencimento": None,
            "chave_acesso_nfe": "",
            "numero_nfe": "",
            "serie_nfe": ""
        }

    valor = extrair_valor_total_nfe(texto) if tipo_detectado == "Nota Fiscal" else maior_valor(texto)

    chave_acesso_nfe = extrair_chave_acesso_nfe(texto) if tipo_detectado == "Nota Fiscal" else ""
    numero_nfe, serie_nfe = extrair_numero_serie_nfe(texto, chave_acesso_nfe) if tipo_detectado == "Nota Fiscal" else ("", "")

    partes_nfe = extrair_emitente_destinatario_nfe(texto) if tipo_detectado == "Nota Fiscal" else {}

    emitente_cnpj = partes_nfe.get("emitente_cnpj", "")
    emitente_nome = partes_nfe.get("emitente_nome", "")
    destinatario_cnpj = partes_nfe.get("destinatario_cnpj", "")
    destinatario_nome = partes_nfe.get("destinatario_nome", "")

    if tipo_detectado == "Nota Fiscal":
        if emitente_cnpj == CNPJ_EMPRESA:
            direcao_sugerida = "Nota Fiscal de Venda"
            parte_cnpj = destinatario_cnpj
            parte_nome = destinatario_nome
        elif destinatario_cnpj == CNPJ_EMPRESA:
            direcao_sugerida = "Nota Fiscal de Compra"
            parte_cnpj = emitente_cnpj
            parte_nome = emitente_nome
        else:
            direcao_sugerida = "Nota Fiscal de Compra"
            parte_cnpj = emitente_cnpj
            parte_nome = emitente_nome
    else:
        direcao_sugerida = tipo_detectado
        cnpjs_sem_empresa = [c for c in cnpjs if c != CNPJ_EMPRESA]
        parte_cnpj = cnpjs_sem_empresa[0] if cnpjs_sem_empresa else ""
        parte_nome = identificar_nome_por_cnpj(texto, parte_cnpj)

    data_emissao = converter_data(datas[0]) if datas else None
    data_vencimento = converter_data(datas[-1]) if datas else None

    return {
        "tipo_detectado": tipo_detectado,
        "direcao_sugerida": direcao_sugerida,
        "cnpjs": cnpjs,
        "parte_cnpj": parte_cnpj,
        "parte_nome": parte_nome,
        "valor": valor,
        "data_emissao": data_emissao,
        "data_vencimento": data_vencimento,
        "chave_acesso_nfe": chave_acesso_nfe,
        "numero_nfe": numero_nfe,
        "serie_nfe": serie_nfe
    }

# =========================
# BANCO ERP
# =========================

def obter_ou_criar_fornecedor(cursor, cnpj, nome):
    cursor.execute("""
        SELECT id
        FROM fornecedores
        WHERE cnpj = ?
          AND empresa_id = ?
    """, (cnpj, EMPRESA_ID_ATIVA))

    resultado = cursor.fetchone()

    if resultado:
        return resultado[0]

    cursor.execute("""
        INSERT INTO fornecedores (
            cnpj,
            nome,
            categoria_padrao,
            tipo_padrao,
            empresa_id
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        cnpj,
        nome,
        "A classificar",
        "Pagar",
        EMPRESA_ID_ATIVA
    ))

    return cursor.lastrowid


def obter_ou_criar_cliente(cursor, cnpj_cpf, nome):
    cursor.execute("""
        SELECT id
        FROM clientes
        WHERE cnpj_cpf = ?
          AND empresa_id = ?
    """, (cnpj_cpf, EMPRESA_ID_ATIVA))

    resultado = cursor.fetchone()

    if resultado:
        return resultado[0]

    cursor.execute("""
        INSERT INTO clientes (
            cnpj_cpf,
            nome,
            empresa_id
        )
        VALUES (?, ?, ?)
    """, (
        cnpj_cpf,
        nome,
        EMPRESA_ID_ATIVA
    ))

    return cursor.lastrowid


def obter_ou_criar_produto(cursor, descricao, custo=0, preco_venda=0):
    cursor.execute("""
        SELECT id
        FROM produtos
        WHERE descricao = ?
          AND empresa_id = ?
    """, (descricao, EMPRESA_ID_ATIVA))

    resultado = cursor.fetchone()

    if resultado:
        produto_id = resultado[0]

        cursor.execute("""
            UPDATE produtos
            SET
                custo_medio = CASE WHEN ? > 0 THEN ? ELSE custo_medio END,
                preco_venda = CASE WHEN ? > 0 THEN ? ELSE preco_venda END
            WHERE id = ?
              AND empresa_id = ?
        """, (
            custo,
            custo,
            preco_venda,
            preco_venda,
            produto_id,
            EMPRESA_ID_ATIVA
        ))

        return produto_id

    cursor.execute("""
        INSERT INTO produtos (
            descricao,
            categoria,
            custo_medio,
            preco_venda,
            empresa_id
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        descricao,
        "A classificar",
        custo,
        preco_venda,
        EMPRESA_ID_ATIVA
    ))

    return cursor.lastrowid


def criar_processo_documental_automatico(
    cursor,
    documento_id,
    tipo_documento,
    direcao,
    parte_cnpj,
    parte_nome,
    valor,
    numero_nfe="",
    serie_nfe=""
):
    cursor.execute("""
        SELECT id
        FROM processos_documentais
        WHERE empresa_id = ?
          AND id IN (
              SELECT processo_id
              FROM processo_documentos
              WHERE documento_id = ?
                AND empresa_id = ?
          )
    """, (
        EMPRESA_ID_ATIVA,
        documento_id,
        EMPRESA_ID_ATIVA
    ))

    existente = cursor.fetchone()

    if existente:
        return existente[0]

    titulo = "Documento ID " + str(documento_id)

    if numero_nfe:
        titulo = f"NF-e {numero_nfe} Série {serie_nfe}"

    if direcao == "Nota Fiscal de Compra":
        tipo_operacao = "Compra"
        papel_empresa = "Destinatário"
        natureza = "Produto"
        proxima_acao = "Anexar comprovante de pagamento"

        pendencias = [
            ("Comprovante de pagamento não localizado", "Comprovante de pagamento"),
            ("Extrato bancário não conciliado", "Extrato bancário")
        ]

    elif direcao == "Nota Fiscal de Venda":
        tipo_operacao = "Venda"
        papel_empresa = "Emitente"
        natureza = "Produto/Serviço"
        proxima_acao = "Confirmar entrega ou execução e prazo de recebimento"

        pendencias = [
            ("Entrega ou execução não confirmada", "Comprovante de entrega/execução"),
            ("Prazo de recebimento não informado", "Prazo de pagamento"),
            ("Recebimento bancário não conciliado", "Extrato bancário")
        ]

    elif direcao == "Boleto / Despesa":
        tipo_operacao = "Despesa"
        papel_empresa = "Pagador"
        natureza = "Despesa"
        proxima_acao = "Anexar comprovante de pagamento"

        pendencias = [
            ("Comprovante de pagamento não localizado", "Comprovante de pagamento"),
            ("Extrato bancário não conciliado", "Extrato bancário")
        ]

    else:
        tipo_operacao = "A classificar"
        papel_empresa = "A classificar"
        natureza = "A classificar"
        proxima_acao = "Classificar documento e definir evidências obrigatórias"

        pendencias = [
            ("Classificação documental pendente", "Classificação manual")
        ]

    cursor.execute("""
        INSERT INTO processos_documentais (
            titulo,
            tipo_operacao,
            papel_empresa,
            natureza,
            contraparte_nome,
            contraparte_cnpj,
            valor_total,
            status,
            proxima_acao,
            empresa_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        titulo,
        tipo_operacao,
        papel_empresa,
        natureza,
        parte_nome,
        parte_cnpj,
        valor,
        "Aberto",
        proxima_acao,
        EMPRESA_ID_ATIVA
    ))

    processo_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO processo_documentos (
            processo_id,
            documento_id,
            tipo_documento,
            obrigatorio,
            status,
            empresa_id
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        processo_id,
        documento_id,
        tipo_documento,
        "Sim",
        "Anexado",
        EMPRESA_ID_ATIVA
    ))

    for descricao, tipo_evidencia in pendencias:
        cursor.execute("""
            INSERT INTO processo_pendencias (
                processo_id,
                descricao,
                tipo_evidencia,
                status,
                empresa_id
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            processo_id,
            descricao,
            tipo_evidencia,
            "Pendente",
            EMPRESA_ID_ATIVA
        ))

    return processo_id



def salvar_documento_erp(nome_arquivo, tipo_documento, direcao, parte_cnpj, parte_nome, valor, data_emissao, data_vencimento, texto, chave_acesso_nfe="", numero_nfe="", serie_nfe=""):
    conn = conectar()
    cursor = conn.cursor()

    if direcao == "Nota Fiscal de Compra":
        cnpj_emitente = parte_cnpj
        nome_emitente = parte_nome
        cnpj_destinatario = CNPJ_EMPRESA
        nome_destinatario = "GODS PRODUTOS, SERVIÇOS & EVENTOS LTDA"
    elif direcao == "Nota Fiscal de Venda":
        cnpj_emitente = CNPJ_EMPRESA
        nome_emitente = "GODS PRODUTOS, SERVIÇOS & EVENTOS LTDA"
        cnpj_destinatario = parte_cnpj
        nome_destinatario = parte_nome
    else:
        cnpj_emitente = parte_cnpj
        nome_emitente = parte_nome
        cnpj_destinatario = ""
        nome_destinatario = ""

    if chave_acesso_nfe:
        cursor.execute("""
            SELECT id
            FROM documentos
            WHERE empresa_id = ?
              AND chave_acesso_nfe = ?
        """, (
            EMPRESA_ID_ATIVA,
            chave_acesso_nfe
        ))
    elif numero_nfe and serie_nfe:
        cursor.execute("""
            SELECT id
            FROM documentos
            WHERE empresa_id = ?
              AND numero_nfe = ?
              AND serie_nfe = ?
              AND IFNULL(cnpj_emitente, '') = ?
              AND IFNULL(cnpj_destinatario, '') = ?
        """, (
            EMPRESA_ID_ATIVA,
            numero_nfe,
            serie_nfe,
            cnpj_emitente or "",
            cnpj_destinatario or ""
        ))
    else:
        cursor.execute("""
            SELECT id
            FROM documentos
            WHERE empresa_id = ?
              AND nome_arquivo = ?
              AND valor = ?
              AND IFNULL(cnpj_emitente, '') = ?
              AND IFNULL(cnpj_destinatario, '') = ?
              AND IFNULL(data_emissao, '') = ?
        """, (
            EMPRESA_ID_ATIVA,
            nome_arquivo,
            abs(valor),
            cnpj_emitente or "",
            cnpj_destinatario or "",
            data_emissao or ""
        ))

    documento_existente = cursor.fetchone()

    if documento_existente:
        conn.close()
        return {
            "documento_id": documento_existente[0],
            "ja_existia": True
        }

    cursor.execute("""
        INSERT INTO documentos (
            nome_arquivo,
            tipo_documento,
            direcao,
            cnpj_emitente,
            nome_emitente,
            cnpj_destinatario,
            nome_destinatario,
            valor,
            data_emissao,
            data_vencimento,
            status_processamento,
            texto_extraido,
            empresa_id,
            chave_acesso_nfe,
            numero_nfe,
            serie_nfe
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        nome_arquivo,
        tipo_documento,
        direcao,
        cnpj_emitente,
        nome_emitente,
        cnpj_destinatario,
        nome_destinatario,
        abs(valor),
        data_emissao,
        data_vencimento,
        "Processado",
        texto,
        EMPRESA_ID_ATIVA,
        chave_acesso_nfe,
        numero_nfe,
        serie_nfe
    ))

    documento_id = cursor.lastrowid

    descricao_operacao = "Documento importado"

    if tipo_documento == "Nota Fiscal":
        descricao_extraida = extrair_descricao_produto_nfe(texto)
        if descricao_extraida:
            descricao_operacao = descricao_extraida

    if direcao in ["Nota Fiscal de Compra", "Boleto / Despesa"]:
        fornecedor_id = obter_ou_criar_fornecedor(cursor, parte_cnpj, parte_nome)
        produto_id = obter_ou_criar_produto(cursor, descricao_operacao, custo=abs(valor), preco_venda=0)

        cursor.execute("""
            INSERT INTO compras (
                fornecedor_id,
                documento_id,
                descricao,
                valor_total,
                data_compra,
                status,
                empresa_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            fornecedor_id,
            documento_id,
            descricao_operacao,
            abs(valor),
            data_emissao,
            "Aberta",
            EMPRESA_ID_ATIVA
        ))

        compra_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO compras_itens (
                compra_id,
                produto_id,
                descricao,
                quantidade,
                valor_unitario,
                valor_total,
                empresa_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            compra_id,
            produto_id,
            descricao_operacao,
            1,
            abs(valor),
            abs(valor),
            EMPRESA_ID_ATIVA
        ))

        cursor.execute("""
            INSERT INTO contas_pagar (
                fornecedor_id,
                documento_id,
                descricao,
                categoria,
                valor,
                data_emissao,
                data_vencimento,
                status,
                empresa_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fornecedor_id,
            documento_id,
            descricao_operacao,
            "Compras",
            abs(valor),
            data_emissao,
            data_vencimento,
            "Pendente",
            EMPRESA_ID_ATIVA
        ))

    elif direcao == "Nota Fiscal de Venda":
        cliente_id = obter_ou_criar_cliente(cursor, parte_cnpj, parte_nome)
        produto_id = obter_ou_criar_produto(cursor, descricao_operacao, custo=0, preco_venda=abs(valor))

        cursor.execute("""
            INSERT INTO vendas (
                cliente_id,
                documento_id,
                descricao,
                valor_total,
                data_venda,
                status,
                empresa_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            cliente_id,
            documento_id,
            descricao_operacao,
            abs(valor),
            data_emissao,
            "Aberta",
            EMPRESA_ID_ATIVA
        ))

        venda_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO vendas_itens (
                venda_id,
                produto_id,
                descricao,
                quantidade,
                valor_unitario,
                valor_total,
                empresa_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            venda_id,
            produto_id,
            descricao_operacao,
            1,
            abs(valor),
            abs(valor),
            EMPRESA_ID_ATIVA
        ))

        cursor.execute("""
            INSERT INTO contas_receber (
                cliente_id,
                documento_id,
                descricao,
                categoria,
                valor,
                data_emissao,
                data_vencimento,
                status,
                empresa_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cliente_id,
            documento_id,
            descricao_operacao,
            "Vendas",
            abs(valor),
            data_emissao,
            data_vencimento,
            "Pendente",
            EMPRESA_ID_ATIVA
        ))

    processo_id = criar_processo_documental_automatico(
        cursor,
        documento_id,
        tipo_documento,
        direcao,
        parte_cnpj,
        parte_nome,
        valor,
        numero_nfe,
        serie_nfe
    )

    conn.commit()
    conn.close()

    return {
        "documento_id": documento_id,
        "ja_existia": False,
        "processo_id": processo_id
    }

# =========================
# INTERFACE
# =========================

if arquivo:
    texto = extrair_texto_pdf(arquivo)
    analise = analisar_documento(texto)

    st.subheader("Triagem do documento")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(f"Tipo detectado: {analise['tipo_detectado']}")

    with col2:
        st.info(f"Valor sugerido: R$ {analise['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    with col3:
        st.info(f"CNPJ identificado: {analise['parte_cnpj'] or 'Não identificado'}")

    if analise["tipo_detectado"] == "Nota Fiscal":
        st.markdown("### Identificação da NF-e")

        col_nf1, col_nf2 = st.columns(2)

        with col_nf1:
            st.text_input("Número NF-e", value=analise["numero_nfe"], disabled=True)

        with col_nf2:
            st.text_input("Série NF-e", value=analise["serie_nfe"], disabled=True)

        st.text_input(
            "Chave de acesso",
            value=formatar_chave_acesso(analise["chave_acesso_nfe"]),
            disabled=True
        )

    with st.form("triagem_erp"):

        direcao = st.selectbox(
            "O que este documento representa?",
            [
                "Nota Fiscal de Compra",
                "Nota Fiscal de Venda",
                "Nota de Empenho",
                "Boleto / Despesa",
                "Comprovante de Pagamento",
                "Comprovante de Recebimento",
                "Extrato Bancário",
                "Cartão CNPJ",
                "A classificar"
            ],
            index=[
                "Nota Fiscal de Compra",
                "Nota Fiscal de Venda",
                "Nota de Empenho",
                "Boleto / Despesa",
                "Comprovante de Pagamento",
                "Comprovante de Recebimento",
                "Extrato Bancário",
                "Cartão CNPJ",
                "A classificar"
            ].index(analise["direcao_sugerida"]) if analise["direcao_sugerida"] in [
                "Nota Fiscal de Compra",
                "Nota Fiscal de Venda",
                "Nota de Empenho",
                "Boleto / Despesa",
                "Comprovante de Pagamento",
                "Comprovante de Recebimento",
                "Extrato Bancário",
                "Cartão CNPJ",
                "A classificar"
            ] else 7
        )

        parte_nome = st.text_input(
            "Fornecedor / Cliente identificado",
            value=analise["parte_nome"]
        )

        parte_cnpj = st.text_input(
            "CNPJ / CPF da outra parte",
            value=analise["parte_cnpj"]
        )

        valor = st.number_input(
            "Valor",
            min_value=0.0,
            value=float(analise["valor"]),
            step=0.01
        )

        data_emissao = st.text_input(
            "Data de emissão",
            value=analise["data_emissao"] or ""
        )

        data_vencimento = st.text_input(
            "Data de vencimento",
            value=analise["data_vencimento"] or ""
        )

        st.text_area(
            "Texto extraído",
            value=texto,
            height=260
        )

        confirmar = st.form_submit_button("Processar no ERP")

    if confirmar:
        resultado = salvar_documento_erp(
            arquivo.name,
            analise["tipo_detectado"],
            direcao,
            parte_cnpj,
            parte_nome,
            valor,
            data_emissao or None,
            data_vencimento or None,
            texto,
            analise["chave_acesso_nfe"],
            analise["numero_nfe"],
            analise["serie_nfe"]
        )

        doc_id = resultado["documento_id"]

        conn = conectar()
        cur = conn.cursor()

        processo_id = resultado.get("processo_id")

        pendencias = []

        if processo_id:
            cur.execute("""
                SELECT descricao
                FROM processo_pendencias
                WHERE processo_id = ?
                  AND status = 'Pendente'
                ORDER BY id
            """, (processo_id,))
            pendencias = [x[0] for x in cur.fetchall()]

        conn.close()

        if processo_id:
            st.divider()
            st.subheader("📌 Processo documental criado")

            st.info(
                f"Processo ID: {processo_id}"
            )

            st.write(f"**Contraparte:** {parte_nome}")
            st.write(f"**Documento:** {arquivo.name}")
            st.write(f"**Valor:** R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

            if pendencias:
                st.warning("Pendências deste processo")

                for p in pendencias:
                    st.write(f"• {p}")

                st.caption(
                    "Estas pendências devem ser resolvidas no próprio fluxo documental."
                )

        if resultado["ja_existia"]:
            st.warning(
                f"Documento já cadastrado anteriormente. Documento ID: {doc_id}. "
                "Nenhuma compra, venda, conta a pagar ou conta a receber foi criada novamente."
            )
        elif direcao in ["Nota de Empenho", "Comprovante de Pagamento", "Comprovante de Recebimento", "Extrato Bancário", "Cartão CNPJ", "A classificar"]:
            st.warning(f"Documento salvo para análise. ID: {doc_id}. Ainda não gerou conta financeira automaticamente.")
        elif direcao == "Nota Fiscal de Compra":
            st.success(f"Nota fiscal de compra processada. Fornecedor cadastrado e conta a pagar criada. Documento ID: {doc_id}.")
        elif direcao == "Nota Fiscal de Venda":
            st.success(f"Nota fiscal de venda processada. Cliente cadastrado e conta a receber criada. Documento ID: {doc_id}.")
        elif direcao == "Boleto / Despesa":
            st.success(f"Boleto/despesa processado. Fornecedor cadastrado e conta a pagar criada. Documento ID: {doc_id}.")