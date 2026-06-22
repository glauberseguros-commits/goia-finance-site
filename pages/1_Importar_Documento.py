import re
import sqlite3
from datetime import datetime

import pytesseract
import streamlit as st
from pdf2image import convert_from_bytes
from pypdf import PdfReader

from utils.auth import empresa_logada, exigir_login
from utils.ui import aplicar_estilo_premium

DB_PATH = "bd/gofinance.db"

exigir_login()
EMPRESA_ID_ATIVA = empresa_logada()

st.set_page_config(page_title="Importar Documento", page_icon="📄", layout="wide")
aplicar_estilo_premium()


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


def conectar():
    return sqlite3.connect(DB_PATH)


def somente_numeros(valor):
    return re.sub(r"\D", "", valor or "")


def normalizar_documento(valor):
    n = somente_numeros(valor)
    if len(n) == 14:
        return f"{n[:2]}.{n[2:5]}.{n[5:8]}/{n[8:12]}-{n[12:]}"
    if len(n) == 11:
        return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}"
    return valor or ""


def moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def obter_empresa_logada():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT nome, cnpj_cpf
        FROM empresas
        WHERE id = ?
    """, (EMPRESA_ID_ATIVA,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return "", ""

    nome, doc = row
    return nome or "", normalizar_documento(doc)


NOME_EMPRESA_LOGADA, DOC_EMPRESA_LOGADA = obter_empresa_logada()


def encontrar_documentos(texto):
    encontrados = re.findall(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}|\d{3}\.?\d{3}\.?\d{3}-?\d{2}", texto or "")
    return list(dict.fromkeys([normalizar_documento(x) for x in encontrados]))


def encontrar_datas(texto):
    return list(dict.fromkeys(re.findall(r"\b\d{2}/\d{2}/\d{4}\b", texto or "")))


def converter_data(valor):
    if not valor:
        return None
    try:
        return datetime.strptime(valor, "%d/%m/%Y").strftime("%Y-%m-%d")
    except Exception:
        return None


def encontrar_valores(texto):
    return list(dict.fromkeys(re.findall(r"\d{1,3}(?:\.\d{3})*,\d{2}", texto or "")))


def converter_valor(valor):
    if not valor:
        return 0.0
    try:
        return float(str(valor).replace("R$", "").replace(" ", "").replace(".", "").replace(",", "."))
    except Exception:
        return 0.0


def maior_valor(texto):
    valores = [converter_valor(v) for v in encontrar_valores(texto)]
    valores = [v for v in valores if v > 0]
    return max(valores) if valores else 0.0


def extrair_texto_pypdf(arquivo):
    arquivo.seek(0)
    reader = PdfReader(arquivo)
    texto = ""
    for page in reader.pages:
        texto += page.extract_text() or ""
        texto += "\n"
    return texto.strip()


def extrair_texto_ocr(arquivo):
    arquivo.seek(0)
    imagens = convert_from_bytes(arquivo.read(), dpi=300)
    texto = ""
    for imagem in imagens:
        texto += pytesseract.image_to_string(imagem, lang="por+eng")
        texto += "\n"
    return texto.strip()


def extrair_texto_pdf(arquivo):
    texto = extrair_texto_pypdf(arquivo)
    if len(texto) < 80:
        texto = extrair_texto_ocr(arquivo)
    return texto


def classificar_tipo_documento(texto):
    t = (texto or "").upper()

    if "NOTA DE EMPENHO" in t or "EMPENHO ORIGINAL" in t or " NE00" in t:
        return "Nota de Empenho"

    if (
        "CADASTRO NACIONAL DA PESSOA JURÍDICA" in t
        or "CADASTRO NACIONAL DA PESSOA JURIDICA" in t
        or "COMPROVANTE DE INSCRIÇÃO E DE SITUAÇÃO CADASTRAL" in t
        or "COMPROVANTE DE INSCRICAO E DE SITUACAO CADASTRAL" in t
    ):
        return "Cartão CNPJ"

    if "DADOS BANCÁRIOS" in t or "DADOS BANCARIOS" in t:
        return "Dados Bancários"

    if "CARTA DE CORREÇÃO ELETRÔNICA" in t or "CARTA DE CORRECAO ELETRONICA" in t:
        return "Carta de Correção NF-e"

    if any(x in t for x in [
        "DANFE",
        "NF-E",
        "NFE",
        "NOTA FISCAL",
        "CHAVE DE ACESSO",
        "DOCUMENTO AUXILIAR DA NOTA FISCAL"
    ]):
        return "Nota Fiscal"

    if "BOLETO" in t or "FICHA DE COMPENSAÇÃO" in t or "PAGÁVEL PREFERENCIALMENTE" in t:
        return "Boleto / Despesa"

    if "COMPROVANTE" in t and any(x in t for x in [
        "PIX",
        "TRANSFERÊNCIA",
        "TRANSFERENCIA",
        "PAGAMENTO",
        "RECEBIMENTO"
    ]):
        if "RECEBIMENTO" in t or "RECEBEMOS" in t:
            return "Comprovante de Recebimento"
        return "Comprovante de Pagamento"

    if "EXTRATO" in t:
        return "Extrato Bancário"

    return "A classificar"

def extrair_chave_acesso_nfe(texto):
    for grupo in re.findall(r"(?:\d{4}\s*){11}", texto or ""):
        chave = somente_numeros(grupo)
        if len(chave) == 44:
            return chave
    return ""


def extrair_numero_serie_nfe(chave):
    chave = somente_numeros(chave)
    if len(chave) != 44:
        return "", ""
    serie = chave[22:25].lstrip("0") or "0"
    numero = chave[25:34].lstrip("0") or "0"
    return numero, serie


def identificar_nome_por_documento(texto, documento):
    if not documento:
        return ""

    linhas = [x.strip() for x in (texto or "").splitlines() if x.strip()]
    doc_limpo = somente_numeros(documento)

    for i, linha in enumerate(linhas):
        if doc_limpo and doc_limpo in somente_numeros(linha):
            candidatos = []
            if i > 0:
                candidatos.append(linhas[i - 1])
            if i > 1:
                candidatos.append(linhas[i - 2])
            if i + 1 < len(linhas):
                candidatos.append(linhas[i + 1])

            for c in candidatos:
                up = c.upper()
                if len(c) >= 5 and "CNPJ" not in up and "CPF" not in up and "CHAVE" not in up:
                    return " ".join(c.split())[:140]

    return ""


def extrair_valor_total_nfe(texto):
    t = texto or ""
    linhas = [x.strip() for x in t.splitlines() if x.strip()]

    rotulos = [
        "V. TOTAL DA NOTA",
        "VALOR TOTAL DA NOTA",
        "VALOR TOTAL DOS PRODUTOS",
        "V. TOTAL DE PRODUTOS",
        "TOTAL DE PRODUTOS",
        "TOTAL DA NOTA"
    ]

    for i, linha in enumerate(linhas):
        if any(r in linha.upper() for r in rotulos):
            janela = " ".join(linhas[i:i + 8])
            valores = [converter_valor(v) for v in encontrar_valores(janela)]
            valores = [v for v in valores if 0 < v < 100000000]
            if valores:
                return max(valores)

    return maior_valor(texto)


def extrair_descricao_produto_nfe(texto):
    linhas = [x.strip() for x in (texto or "").splitlines() if x.strip()]
    palavras = ["NOTEBOOK", "MAQUINA", "MÁQUINA", "SERVIÇO", "SERVICO", "PRODUTO"]

    for linha in linhas:
        if any(p in linha.upper() for p in palavras):
            return " ".join(linha.replace("[", " ").replace("]", " ").split())[:180]

    return "Documento importado"


def extrair_documento_do_bloco(bloco):
    bloco = bloco or ""

    padroes = [
        r"CNPJ\s*/\s*CPF\s*[:\-]?\s*(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})",
        r"CNPJ\s*[:\-]?\s*(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})",
        r"CPF\s*[:\-]?\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})",
        r"\b(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})\b",
        r"\b(\d{3}\.?\d{3}\.?\d{3}-?\d{2})\b",
    ]

    for padrao in padroes:
        m = re.search(padrao, bloco, flags=re.I)
        if m:
            return normalizar_documento(m.group(1))

    return ""


def extrair_nome_do_bloco(bloco):
    linhas = [x.strip() for x in (bloco or "").splitlines() if x.strip()]

    ignorar = [
        "DANFE", "DOCUMENTO AUXILIAR", "NF-E", "NFE",
        "DESTINATÁRIO", "DESTINATARIO", "REMETENTE", "EMITENTE",
        "NOME / RAZÃO SOCIAL", "NOME / RAZAO SOCIAL",
        "CNPJ", "CPF", "ENDEREÇO", "ENDERECO", "BAIRRO", "CEP",
        "MUNICÍPIO", "MUNICIPIO", "UF", "FONE", "FAX",
        "INSCRIÇÃO ESTADUAL", "INSCRICAO ESTADUAL",
        "DATA DA EMISSÃO", "DATA DA EMISSAO", "DATA DA SAÍDA", "DATA DA SAIDA",
        "CHAVE DE ACESSO", "PROTOCOLO", "AUTORIZAÇÃO", "AUTORIZACAO",
        "CONSULTA DE AUTENTICIDADE", "WWW.NFE", "WWW.FAZENDA",
        "NATUREZA DA OPERAÇÃO", "NATUREZA DA OPERACAO",
        "SÉRIE", "SERIE", "FOLHA", "SAÍDA", "SAIDA", "ENTRADA"
    ]

    def linha_valida(linha):
        up = linha.upper()

        if len(linha.strip()) < 5:
            return False

        if any(x in up for x in ignorar):
            return False

        if re.search(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}", linha):
            return False

        if re.search(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}", linha):
            return False

        if len(re.sub(r"\D", "", linha)) >= 8:
            return False

        return True

    # 1) Preferência: linha após NOME / RAZÃO SOCIAL.
    for i, linha in enumerate(linhas):
        up = linha.upper()

        if "NOME / RAZÃO SOCIAL" in up or "NOME / RAZAO SOCIAL" in up:
            for prox in linhas[i + 1:i + 6]:
                if linha_valida(prox):
                    return " ".join(prox.split())[:140]

    # 2) Fallback: primeira linha textual válida do bloco.
    for linha in linhas:
        if linha_valida(linha):
            return " ".join(linha.split())[:140]

    return ""

def extrair_email_do_bloco(bloco):
    m = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", bloco or "")
    return m.group(0) if m else ""


def extrair_cidade_uf_do_bloco(bloco):
    linhas = [x.strip() for x in (bloco or "").splitlines() if x.strip()]
    ufs = "AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO"

    for linha in linhas:
        m = re.search(rf"\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ\s]+)\s+({ufs})\b", linha.upper())
        if m:
            cidade = " ".join(m.group(1).split()).title()
            uf = m.group(2)
            return cidade, uf

    return "", ""


def cortar_bloco(texto, inicio_tokens, fim_tokens):
    linhas = [x.rstrip() for x in (texto or "").splitlines()]
    inicio = None

    for i, linha in enumerate(linhas):
        up = linha.upper()
        if any(tok in up for tok in inicio_tokens):
            inicio = i
            break

    if inicio is None:
        return ""

    fim = len(linhas)

    for j in range(inicio + 1, len(linhas)):
        up = linhas[j].upper()
        if any(tok in up for tok in fim_tokens):
            fim = j
            break

    return "\n".join(linhas[inicio:fim])


def extrair_bloco_emitente_nfe(texto):
    linhas = [x.rstrip() for x in (texto or "").splitlines()]

    idx_dest = None
    for i, linha in enumerate(linhas):
        up = linha.upper()
        if "DESTINATÁRIO" in up or "DESTINATARIO" in up or "REMETENTE" in up:
            idx_dest = i
            break

    trecho = "\n".join(linhas[:idx_dest]) if idx_dest is not None else "\n".join(linhas)

    # Se existir uma linha com CNPJ antes do destinatário, usa uma janela ao redor dela.
    docs = encontrar_documentos(trecho)
    if DOC_EMPRESA_LOGADA in docs:
        doc_ref = DOC_EMPRESA_LOGADA
    else:
        doc_ref = docs[0] if docs else ""

    if doc_ref:
        doc_limpo = somente_numeros(doc_ref)
        for i, linha in enumerate(trecho.splitlines()):
            if doc_limpo in somente_numeros(linha):
                ini = max(0, i - 6)
                fim = min(len(trecho.splitlines()), i + 8)
                return "\n".join(trecho.splitlines()[ini:fim])

    return trecho

def extrair_bloco_destinatario_nfe(texto):
    bloco = cortar_bloco(
        texto,
        ["DESTINATÁRIO", "DESTINATARIO", "REMETENTE"],
        [
            "PAGAMENTOS",
            "CÁLCULO DO IMPOSTO",
            "CALCULO DO IMPOSTO",
            "TRANSPORTADOR",
            "DADOS DOS PRODUTOS",
            "DADOS ADICIONAIS",
            "FATURA",
            "DUPLICATA"
        ]
    )

    if bloco:
        return bloco

    # Fallback conservador: se não achou cabeçalho, não inventa destinatário.
    return ""

def extrair_cadastro_do_bloco(bloco):
    cidade, uf = extrair_cidade_uf_do_bloco(bloco)

    return {
        "doc": extrair_documento_do_bloco(bloco),
        "nome": extrair_nome_do_bloco(bloco),
        "email": extrair_email_do_bloco(bloco),
        "cidade": cidade,
        "uf": uf,
        "bloco": bloco,
    }

def extrair_partes_nfe(texto):
    documentos = encontrar_documentos(texto)
    t = (texto or "").upper()

    emitente_doc = ""
    emitente_nome = ""
    destinatario_doc = ""
    destinatario_nome = ""

    chave = extrair_chave_acesso_nfe(texto)

    # Na NF-e, o CNPJ do emitente fica nas posições 7 a 20 da chave de acesso.
    # Exemplo:
    # 53 2511 28860122000177 55 001 000000032 ...
    if chave and len(chave) == 44:
        cnpj_emitente_chave = normalizar_documento(chave[6:20])

        if cnpj_emitente_chave:
            emitente_doc = cnpj_emitente_chave

            if somente_numeros(emitente_doc) == somente_numeros(DOC_EMPRESA_LOGADA):
                emitente_nome = NOME_EMPRESA_LOGADA
            else:
                emitente_nome = identificar_nome_por_documento(texto, emitente_doc)

    # Fallback: se não conseguiu pela chave, usa documentos encontrados no texto.
    if not emitente_doc:
        for doc in documentos:
            if somente_numeros(doc) == somente_numeros(DOC_EMPRESA_LOGADA):
                emitente_doc = DOC_EMPRESA_LOGADA
                emitente_nome = NOME_EMPRESA_LOGADA
                break

    # Destinatário: primeiro documento válido diferente do emitente e da empresa logada.
    candidatos_destinatario = []

    for doc in documentos:
        doc_num = somente_numeros(doc)

        if emitente_doc and doc_num == somente_numeros(emitente_doc):
            continue

        candidatos_destinatario.append(doc)

    if candidatos_destinatario:
        # Se a empresa logada aparecer entre os candidatos, ela é destinatária.
        for doc in candidatos_destinatario:
            if somente_numeros(doc) == somente_numeros(DOC_EMPRESA_LOGADA):
                destinatario_doc = DOC_EMPRESA_LOGADA
                destinatario_nome = NOME_EMPRESA_LOGADA
                break

        # Caso contrário, pega o primeiro externo como contraparte.
        if not destinatario_doc:
            destinatario_doc = candidatos_destinatario[0]
            destinatario_nome = identificar_nome_por_documento(texto, destinatario_doc)

    # Heurísticas de nome úteis para órgãos/clientes conhecidos.
    if "COMANDO DA MARINHA" in t:
        destinatario_nome = "COMANDO DA MARINHA"

    if "ADMINISTRAÇÃO REGIONAL DE SOBRADINHO" in t or "ADMINISTRACAO REGIONAL DE SOBRADINHO" in t:
        destinatario_nome = "ADMINISTRAÇÃO REGIONAL DE SOBRADINHO"

    if "EVENTOS LTDA" in t and not destinatario_nome and destinatario_doc:
        destinatario_nome = "EVENTOS LTDA"

    if "PONTO CERTO" in t and not emitente_nome:
        emitente_nome = "PONTO CERTO COMERCIO DE FERRAGENS LTDA"

    return {
        "emitente_doc": emitente_doc,
        "emitente_nome": emitente_nome,
        "destinatario_doc": destinatario_doc,
        "destinatario_nome": destinatario_nome,
    }


def extrair_entidades_documento(texto):
    texto = texto or ""
    documentos = encontrar_documentos(texto)

    emails = re.findall(
        r"[\w\.-]+@[\w\.-]+\.\w+",
        texto,
        flags=re.I
    )
    emails = list(dict.fromkeys([e.strip().lower() for e in emails]))

    telefones_raw = re.findall(
        r"(?:\(?\d{2}\)?\s*)?(?:9\s*)?\d{4}[-\s]?\d{4}",
        texto
    )

    telefones = []
    for tel in telefones_raw:
        nums = somente_numeros(tel)
        if 8 <= len(nums) <= 11:
            telefones.append(nums)

    nomes = []
    linhas = [x.strip() for x in texto.splitlines() if x.strip()]

    for doc in documentos:
        nome = identificar_nome_por_documento(texto, doc)
        if nome:
            nomes.append(nome)

    palavras_ruido = [
        "DANFE", "DOCUMENTO AUXILIAR", "CHAVE DE ACESSO",
        "PROTOCOLO", "CONSULTA", "AUTENTICIDADE",
        "NATUREZA DA OPERAÇÃO", "NATUREZA DA OPERACAO",
        "CNPJ", "CPF", "INSCRIÇÃO", "INSCRICAO",
        "ENDEREÇO", "ENDERECO", "BAIRRO", "CEP",
        "MUNICÍPIO", "MUNICIPIO", "UF", "FONE", "FAX",
        "DATA", "HORA", "VALOR", "TOTAL", "PRODUTO",
        "CÁLCULO", "CALCULO", "IMPOSTO", "TRANSPORTADOR"
    ]

    for linha in linhas:
        up = linha.upper()

        if any(r in up for r in palavras_ruido):
            continue

        if len(somente_numeros(linha)) >= 8:
            continue

        if len(linha) >= 5 and any(c.isalpha() for c in linha):
            nomes.append(" ".join(linha.split())[:140])

    return {
        "documentos": documentos,
        "emails": emails,
        "telefones": list(dict.fromkeys(telefones)),
        "nomes_possiveis": list(dict.fromkeys(nomes))[:10],
    }

def analisar_documento(texto):
    tipo = classificar_tipo_documento(texto)
    documentos = encontrar_documentos(texto)
    entidades = extrair_entidades_documento(texto)
    datas = encontrar_datas(texto)

    chave = extrair_chave_acesso_nfe(texto) if tipo == "Nota Fiscal" else ""
    numero, serie = extrair_numero_serie_nfe(chave)

    parte_doc = ""
    parte_nome = ""
    direcao = tipo

    emitente_doc = ""
    emitente_nome = ""
    destinatario_doc = ""
    destinatario_nome = ""

    if tipo == "Nota Fiscal":
        partes = extrair_partes_nfe(texto)

        emitente_doc = partes.get("emitente_doc") or ""
        emitente_nome = partes.get("emitente_nome") or ""
        destinatario_doc = partes.get("destinatario_doc") or ""
        destinatario_nome = partes.get("destinatario_nome") or ""

        if emitente_doc == DOC_EMPRESA_LOGADA and destinatario_doc and destinatario_nome:
            direcao = "Nota Fiscal de Venda"
            parte_doc = destinatario_doc
            parte_nome = destinatario_nome

        elif destinatario_doc == DOC_EMPRESA_LOGADA and emitente_doc and emitente_nome:
            direcao = "Nota Fiscal de Compra"
            parte_doc = emitente_doc
            parte_nome = emitente_nome

        else:
            direcao = "Nota Fiscal - Conferência necessária"
            parte_doc = destinatario_doc or emitente_doc
            parte_nome = destinatario_nome or emitente_nome

        valor = extrair_valor_total_nfe(texto)

    elif tipo == "Nota de Empenho":
        t = (texto or "").upper()
        valor = maior_valor(texto)

        parte_nome = "Órgão Público"

        parte_doc = ""

    elif tipo == "Cartão CNPJ":
        valor = 0
        docs = encontrar_documentos(texto)
        parte_doc = docs[0] if docs else ""

        m_nome = re.search(r"NOME EMPRESARIAL\s+(.+)", texto or "", flags=re.I)
        if m_nome:
            parte_nome = " ".join(m_nome.group(1).split())[:140]

    else:
        valor = maior_valor(texto)
        parte_doc = ""
        parte_nome = ""

    return {
        "tipo_detectado": tipo,
        "direcao_sugerida": direcao,
        "documentos_encontrados": documentos,
        "entidades_extraidas": entidades,
        "parte_cnpj": parte_doc,
        "parte_nome": parte_nome,
        "valor": valor,
        "data_emissao": converter_data(datas[0]) if datas else None,
        "data_vencimento": converter_data(datas[-1]) if datas else None,
        "chave_acesso_nfe": chave,
        "numero_nfe": numero,
        "serie_nfe": serie,
        "emitente_cnpj": emitente_doc,
        "emitente_nome": emitente_nome,
        "destinatario_cnpj": destinatario_doc,
        "destinatario_nome": destinatario_nome,
    }

def obter_ou_criar_cliente(cursor, documento, nome):
    documento = normalizar_documento(documento)
    nome = (nome or "").strip()

    if not documento and not nome:
        return None

    if documento:
        cursor.execute("""
            SELECT id FROM clientes
            WHERE empresa_id = ? AND cnpj_cpf = ?
        """, (EMPRESA_ID_ATIVA, documento))
    else:
        cursor.execute("""
            SELECT id FROM clientes
            WHERE empresa_id = ? AND nome = ?
        """, (EMPRESA_ID_ATIVA, nome))

    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute("""
        INSERT INTO clientes (empresa_id, nome, cnpj_cpf, origem_cadastro)
        VALUES (?, ?, ?, ?)
    """, (EMPRESA_ID_ATIVA, nome or "Cliente não identificado", documento, "Importação documental"))

    return cursor.lastrowid


def obter_ou_criar_fornecedor(cursor, documento, nome):
    documento = normalizar_documento(documento)
    nome = (nome or "").strip()

    if not documento and not nome:
        return None

    if documento:
        cursor.execute("""
            SELECT id FROM fornecedores
            WHERE empresa_id = ? AND cnpj = ?
        """, (EMPRESA_ID_ATIVA, documento))
    else:
        cursor.execute("""
            SELECT id FROM fornecedores
            WHERE empresa_id = ? AND nome = ?
        """, (EMPRESA_ID_ATIVA, nome))

    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute("""
        INSERT INTO fornecedores (
            empresa_id, nome, cnpj, categoria_padrao, tipo_padrao, origem_cadastro
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        EMPRESA_ID_ATIVA,
        nome or "Fornecedor não identificado",
        documento,
        "A classificar",
        "Pagar",
        "Importação documental"
    ))

    return cursor.lastrowid


def obter_ou_criar_produto(cursor, descricao, custo=0, preco_venda=0):
    descricao = descricao or "Documento importado"

    cursor.execute("""
        SELECT id FROM produtos
        WHERE empresa_id = ? AND descricao = ?
    """, (EMPRESA_ID_ATIVA, descricao))

    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute("""
        INSERT INTO produtos (empresa_id, descricao, categoria, custo_medio, preco_venda)
        VALUES (?, ?, ?, ?, ?)
    """, (EMPRESA_ID_ATIVA, descricao, "A classificar", custo, preco_venda))

    return cursor.lastrowid



def criar_evidencia_documental(cursor, processo_id, documento_id, analise, conta_receber_id=None, conta_pagar_id=None):
    tipo = analise.get("tipo_detectado") or "Documento"
    numero = analise.get("numero_nfe") or ""
    serie = analise.get("serie_nfe") or ""
    valor = float(analise.get("valor") or 0)
    data_ref = analise.get("data_emissao") or analise.get("data_vencimento")
    origem = "Importação documental"

    descricao = tipo

    if numero:
        descricao = f"{tipo} {numero}"
        if serie:
            descricao += f" Série {serie}"

    cursor.execute("""
        INSERT INTO evidencias (
            empresa_id,
            processo_id,
            documento_id,
            conta_receber_id,
            conta_pagar_id,
            tipo_evidencia,
            descricao,
            origem,
            valor,
            data_referencia,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        EMPRESA_ID_ATIVA,
        processo_id,
        documento_id,
        conta_receber_id,
        conta_pagar_id,
        tipo,
        descricao,
        origem,
        valor,
        data_ref,
        "Ativa"
    ))

    evidencia_id = cursor.lastrowid

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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        EMPRESA_ID_ATIVA,
        processo_id,
        documento_id,
        tipo,
        descricao,
        valor,
        data_ref,
        origem,
        "Validada"
    ))

    return evidencia_id

def criar_processo_documental(cursor, documento_id, analise):
    direcao = analise["direcao_sugerida"]

    if direcao == "Nota Fiscal de Venda":
        tipo_operacao = "Venda"
        papel_empresa = "Emitente"
        pendencias = [
            ("Entrega ou execução não confirmada", "Comprovante de entrega/execução"),
            ("Recebimento bancário não conciliado", "Extrato bancário"),
        ]
    elif direcao == "Nota Fiscal de Compra":
        tipo_operacao = "Compra"
        papel_empresa = "Destinatário"
        pendencias = [
            ("Comprovante de pagamento não localizado", "Comprovante de pagamento"),
            ("Extrato bancário não conciliado", "Extrato bancário"),
        ]
    else:
        tipo_operacao = "A classificar"
        papel_empresa = "A classificar"
        pendencias = [("Classificação documental pendente", "Classificação manual")]

    titulo = f"Documento ID {documento_id}"
    if analise.get("numero_nfe"):
        titulo = f"NF-e {analise['numero_nfe']} Série {analise.get('serie_nfe') or ''}"

    cursor.execute("""
        INSERT INTO processos_documentais (
            titulo, tipo_operacao, papel_empresa, natureza,
            contraparte_nome, contraparte_cnpj, valor_total,
            status, proxima_acao, empresa_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        titulo,
        tipo_operacao,
        papel_empresa,
        "Produto/Serviço",
        analise.get("parte_nome") or "",
        analise.get("parte_cnpj") or "",
        analise.get("valor") or 0,
        "Aberto",
        "Resolver pendências documentais",
        EMPRESA_ID_ATIVA
    ))

    processo_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO processo_documentos (
            processo_id, documento_id, tipo_documento, obrigatorio, status, empresa_id
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        processo_id,
        documento_id,
        analise.get("tipo_detectado") or "Documento",
        "Sim",
        "Anexado",
        EMPRESA_ID_ATIVA
    ))

    for descricao, tipo_evidencia in pendencias:
        cursor.execute("""
            INSERT INTO processo_pendencias (
                processo_id, descricao, tipo_evidencia, status, empresa_id
            )
            VALUES (?, ?, ?, ?, ?)
        """, (processo_id, descricao, tipo_evidencia, "Pendente", EMPRESA_ID_ATIVA))

    return processo_id


def salvar_documento_erp(nome_arquivo, texto, analise):
    conn = conectar()
    cur = conn.cursor()

    direcao = analise["direcao_sugerida"]
    tipo = analise["tipo_detectado"]
    valor = abs(float(analise.get("valor") or 0))
    parte_doc = analise.get("parte_cnpj") or ""
    parte_nome = analise.get("parte_nome") or ""

    if direcao == "Nota Fiscal de Venda":
        cnpj_emitente = DOC_EMPRESA_LOGADA
        nome_emitente = NOME_EMPRESA_LOGADA
        cnpj_destinatario = parte_doc
        nome_destinatario = parte_nome
    elif direcao == "Nota Fiscal de Compra":
        cnpj_emitente = parte_doc
        nome_emitente = parte_nome
        cnpj_destinatario = DOC_EMPRESA_LOGADA
        nome_destinatario = NOME_EMPRESA_LOGADA
    else:
        cnpj_emitente = parte_doc
        nome_emitente = parte_nome
        cnpj_destinatario = ""
        nome_destinatario = ""

    if analise.get("chave_acesso_nfe"):
        cur.execute("""
            SELECT id FROM documentos
            WHERE empresa_id = ? AND chave_acesso_nfe = ?
        """, (EMPRESA_ID_ATIVA, analise["chave_acesso_nfe"]))
    else:
        cur.execute("""
            SELECT id FROM documentos
            WHERE empresa_id = ?
              AND nome_arquivo = ?
              AND IFNULL(valor, 0) = ?
        """, (EMPRESA_ID_ATIVA, nome_arquivo, valor))

    existente = cur.fetchone()

    if existente:
        documento_id = existente[0]
        acoes = ["Documento já existia. Não foi duplicado."]
        conn.close()
        return {
            "documento_id": documento_id,
            "processo_id": None,
            "ja_existia": True,
            "acoes": acoes
        }

    cur.execute("""
        INSERT INTO documentos (
            nome_arquivo, tipo_documento, direcao,
            cnpj_emitente, nome_emitente, cnpj_destinatario, nome_destinatario,
            valor, data_emissao, data_vencimento,
            status_processamento, texto_extraido, empresa_id,
            chave_acesso_nfe, numero_nfe, serie_nfe
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        nome_arquivo,
        tipo,
        direcao,
        cnpj_emitente,
        nome_emitente,
        cnpj_destinatario,
        nome_destinatario,
        valor,
        analise.get("data_emissao"),
        analise.get("data_vencimento"),
        "Processado",
        texto,
        EMPRESA_ID_ATIVA,
        analise.get("chave_acesso_nfe") or "",
        analise.get("numero_nfe") or "",
        analise.get("serie_nfe") or ""
    ))

    documento_id = cur.lastrowid
    conta_receber_id = None
    conta_pagar_id = None
    acoes = ["Documento salvo."]

    descricao = extrair_descricao_produto_nfe(texto)

    if direcao == "Nota Fiscal de Venda":
        cliente_id = obter_ou_criar_cliente(cur, parte_doc, parte_nome)
        produto_id = obter_ou_criar_produto(cur, descricao, custo=0, preco_venda=valor)

        if cliente_id:
            acoes.append("Cliente criado/identificado.")

            cur.execute("""
                INSERT INTO vendas (
                    cliente_id, documento_id, descricao, valor_total, data_venda, status, empresa_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (cliente_id, documento_id, descricao, valor, analise.get("data_emissao"), "Aberta", EMPRESA_ID_ATIVA))

            venda_id = cur.lastrowid

            cur.execute("""
                INSERT INTO vendas_itens (
                    venda_id, produto_id, descricao, quantidade, valor_unitario, valor_total, empresa_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (venda_id, produto_id, descricao, 1, valor, valor, EMPRESA_ID_ATIVA))

            cur.execute("""
                INSERT INTO contas_receber (
                    cliente_id, documento_id, descricao, categoria, valor,
                    data_emissao, data_vencimento, status, empresa_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cliente_id, documento_id, descricao, "Vendas", valor,
                analise.get("data_emissao"), analise.get("data_vencimento"), "Pendente", EMPRESA_ID_ATIVA
            ))

            conta_receber_id = cur.lastrowid

            acoes.append("Venda e conta a receber criadas.")

    elif direcao in ["Nota Fiscal de Compra", "Boleto / Despesa"]:
        fornecedor_id = obter_ou_criar_fornecedor(cur, parte_doc, parte_nome)
        produto_id = obter_ou_criar_produto(cur, descricao, custo=valor, preco_venda=0)

        if fornecedor_id:
            acoes.append("Fornecedor criado/identificado.")

            cur.execute("""
                INSERT INTO compras (
                    fornecedor_id, documento_id, descricao, valor_total, data_compra, status, empresa_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (fornecedor_id, documento_id, descricao, valor, analise.get("data_emissao"), "Aberta", EMPRESA_ID_ATIVA))

            compra_id = cur.lastrowid

            cur.execute("""
                INSERT INTO compras_itens (
                    compra_id, produto_id, descricao, quantidade, valor_unitario, valor_total, empresa_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (compra_id, produto_id, descricao, 1, valor, valor, EMPRESA_ID_ATIVA))

            cur.execute("""
                INSERT INTO contas_pagar (
                    fornecedor_id, documento_id, descricao, categoria, valor,
                    data_emissao, data_vencimento, status, empresa_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fornecedor_id, documento_id, descricao, "Compras", valor,
                analise.get("data_emissao"), analise.get("data_vencimento"), "Pendente", EMPRESA_ID_ATIVA
            ))

            conta_pagar_id = cur.lastrowid

            acoes.append("Compra e conta a pagar criadas.")

    elif direcao == "Nota de Empenho":
        cliente_id = obter_ou_criar_cliente(cur, parte_doc, parte_nome)
        if cliente_id:
            acoes.append("Cliente criado/identificado pela nota de empenho.")

    processo_id = criar_processo_documental(cur, documento_id, analise)

    criar_evidencia_documental(
        cur,
        processo_id,
        documento_id,
        analise,
        conta_receber_id=conta_receber_id,
        conta_pagar_id=conta_pagar_id
    )

    acoes.append("Processo documental, evidência e pendências criados.")

    conn.commit()
    conn.close()

    return {
        "documento_id": documento_id,
        "processo_id": processo_id,
        "ja_existia": False,
        "acoes": acoes
    }


st.title("📄 Importar Documento Financeiro")
st.caption("Envie NF-e, nota de empenho, comprovantes, boletos, extratos e cadastros. A GOIA classifica e cria o fluxo financeiro.")

if not DOC_EMPRESA_LOGADA:
    st.error("Empresa logada sem CPF/CNPJ cadastrado. Corrija o cadastro da empresa antes de importar documentos.")
    st.stop()

arquivos = st.file_uploader(
    "Anexar documentos",
    type=["pdf", "ofx", "csv", "txt", "xml"],
    accept_multiple_files=True
)

if not arquivos:
    st.info("Anexe um ou mais documentos para iniciar.")
    st.stop()

st.info(f"{len(arquivos)} documento(s) anexado(s). Todos serão analisados e processados.")

if st.button("Processar todos os documentos", type="primary"):
    for arquivo in arquivos:
        with st.container(border=True):
            st.markdown(f"### 📄 {arquivo.name}")

            try:
                texto = extrair_texto_pdf(arquivo)
                analise = analisar_documento(texto)

                c1, c2, c3 = st.columns(3)
                c1.metric("Tipo", analise["tipo_detectado"])
                c2.metric("Classificação", analise["direcao_sugerida"])
                c3.metric("Valor", moeda(analise["valor"]))

                st.write(f"**Contraparte:** {analise.get('parte_nome') or 'Não identificada'}")
                st.write(f"**Documento contraparte:** {analise.get('parte_cnpj') or 'Não identificado'}")

                with st.expander("Diagnóstico técnico"):
                    st.json(analise)

                entidades = analise.get("entidades_extraidas", {})

                if entidades:
                    with st.expander("Entidades encontradas no documento"):
                        st.write("**Documentos encontrados:**", entidades.get("documentos", []))
                        st.write("**E-mails encontrados:**", entidades.get("emails", []))
                        st.write("**Telefones encontrados:**", entidades.get("telefones", []))
                        st.write("**Nomes possíveis:**", entidades.get("nomes_possiveis", []))
                        st.write("**Cidades/UF possíveis:**", entidades.get("cidades_ufs", []))

                resultado = salvar_documento_erp(arquivo.name, texto, analise)

                if resultado.get("ja_existia"):
                    st.warning(f"Documento já existia. ID: {resultado['documento_id']}")
                else:
                    st.success(f"Documento processado. ID: {resultado['documento_id']}")

                for acao in resultado.get("acoes", []):
                    st.write(f"✓ {acao}")

                if resultado.get("processo_id"):
                    st.info(f"Processo documental criado: {resultado['processo_id']}")

            except Exception as e:
                st.error(f"Erro ao processar documento: {e}")
