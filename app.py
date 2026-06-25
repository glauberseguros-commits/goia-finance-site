import json
import urllib.request
import os
import hashlib
import re
from io import BytesIO

import pandas as pd
import streamlit as st

from utils.ui import aplicar_estilo_premium
from utils.premium import aplicar_premium_goia, hero, kpi_card, section_title
from utils.padronizadores import limpar_cnpj, limpar_telefone, telefone_valido, formatar_telefone
from utils.db import caminho_banco, conectar_banco
from utils.schema import inicializar_schema_goia


DB_PATH = caminho_banco()

st.set_page_config(
    page_title="GOIA Finance Platform",
    page_icon="💰",
    layout="wide"
)

aplicar_estilo_premium()
aplicar_premium_goia()

st.markdown("""
<style>
[data-testid="stSidebarNav"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)


def conectar():
    return conectar_banco()


def hash_senha(s):
    return hashlib.sha256(str(s).encode("utf-8")).hexdigest()


def moeda(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def normalizar_capital_social(valor):
    if valor is None:
        return 0.0

    txt = str(valor).strip()
    if not txt:
        return 0.0

    txt = txt.replace("R$", "").replace(" ", "")

    if "," in txt:
        txt = txt.replace(".", "").replace(",", ".")

    try:
        return float(txt)
    except Exception:
        return 0.0


def formatar_cnpj(valor):
    numeros = re.sub(r"\D", "", valor or "")
    if len(numeros) == 14:
        return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"
    return valor or ""


def texto_padrao(v):
    return str(v or "").strip()


def empresa_existe_por_cnpj(cnpj):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nome, senha_hash
        FROM empresas
        WHERE REPLACE(REPLACE(REPLACE(REPLACE(cnpj_cpf,'.',''),'/',''),'-',''),' ','') = ?
        LIMIT 1
    """, (limpar_cnpj(cnpj),))

    row = cur.fetchone()
    conn.close()

    if row:
        return {"id": row[0], "nome": row[1], "senha_hash": row[2]}

    return None


def buscar_empresa(cnpj, senha):
    conn = conectar()
    conn.row_factory = None
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nome, cnpj_cpf
        FROM empresas
        WHERE REPLACE(REPLACE(REPLACE(REPLACE(cnpj_cpf,'.',''),'/',''),'-',''),' ','') = ?
          AND senha_hash = ?
          AND COALESCE(status_assinatura, 'Ativa') = 'Ativa'
        LIMIT 1
    """, (limpar_cnpj(cnpj), hash_senha(senha)))

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {"id": row[0], "nome": row[1], "cnpj_cpf": row[2]}


def extrair_dados_cartao_cnpj_pdf(arquivo):
    dados = {
        "nome": "",
        "nome_fantasia": "",
        "cnpj": "",
        "email": "",
        "telefone": "",
    }

    try:
        from pypdf import PdfReader

        arquivo.seek(0)
        reader = PdfReader(BytesIO(arquivo.read()))

        texto = ""
        for page in reader.pages:
            texto += page.extract_text() or ""
            texto += "\n"

    except Exception:
        return dados

    texto_sem_espacos = re.sub(r"\s+", "", texto)

    m = re.search(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}", texto_sem_espacos)
    if m:
        dados["cnpj"] = formatar_cnpj(m.group())

    linhas = [x.strip() for x in texto.splitlines() if x.strip()]

    for i, linha in enumerate(linhas):
        if "NOME EMPRESARIAL" in linha.upper() and i + 1 < len(linhas):
            dados["nome"] = linhas[i + 1].strip()
            break

    for i, linha in enumerate(linhas):
        if "TÍTULO DO ESTABELECIMENTO" in linha.upper() and i + 1 < len(linhas):
            dados["nome_fantasia"] = linhas[i + 1].strip()
            break

    email = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", texto)
    if email:
        dados["email"] = email.group()

    telefone = re.search(r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}", texto)
    if telefone:
        dados["telefone"] = telefone.group()

    return dados


def consultar_cnpj_publica_ws(cnpj):
    cnpj_limpo = limpar_cnpj(cnpj)

    if not cnpj_limpo or len(cnpj_limpo) != 14:
        return {}

    try:
        req = urllib.request.Request(
            f"https://publica.cnpj.ws/cnpj/{cnpj_limpo}",
            headers={"User-Agent": "GOIA-Finance/1.0"}
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            bruto = resp.read().decode("utf-8")
            data = json.loads(bruto)

        est = data.get("estabelecimento") or {}
        cidade = est.get("cidade") or {}
        estado = est.get("estado") or {}
        atividade_principal = est.get("atividade_principal") or {}
        atividades_secundarias = est.get("atividades_secundarias") or []
        socios = data.get("socios") or []

        cnaes_secundarios = []
        for item in atividades_secundarias:
            codigo = str(item.get("subclasse") or item.get("id") or "").strip()
            descricao = str(item.get("descricao") or "").strip()
            if codigo or descricao:
                cnaes_secundarios.append(f"{codigo} - {descricao}".strip(" -"))

        qsa = []
        for socio in socios:
            nome = str(socio.get("nome") or "").strip()
            qualificacao = str((socio.get("qualificacao_socio") or {}).get("descricao") or "").strip()
            if nome:
                qsa.append(f"{nome} - {qualificacao}".strip(" -"))

        return {
            "nome": data.get("razao_social") or "",
            "nome_fantasia": est.get("nome_fantasia") or "",
            "cnpj": cnpj_limpo,
            "situacao_cadastral": est.get("situacao_cadastral") or "",
            "data_abertura": est.get("data_inicio_atividade") or "",
            "porte": (data.get("porte") or {}).get("descricao") or "",
            "natureza_juridica": (data.get("natureza_juridica") or {}).get("descricao") or "",
            "capital_social": data.get("capital_social") or "",
            "cnae_principal": f"{atividade_principal.get('subclasse') or ''} - {atividade_principal.get('descricao') or ''}".strip(" -"),
            "cnaes_secundarios": "\n".join(cnaes_secundarios),
            "cep": est.get("cep") or "",
            "logradouro": est.get("logradouro") or "",
            "numero": est.get("numero") or "",
            "complemento": est.get("complemento") or "",
            "bairro": est.get("bairro") or "",
            "municipio": cidade.get("nome") or "",
            "uf": estado.get("sigla") or "",
            "email": est.get("email") or "",
            "telefone": f"{est.get('ddd1') or ''}{est.get('telefone1') or ''}",
            "qsa": "\n".join(qsa),
            "dados_cnpj_json": json.dumps(data, ensure_ascii=False),
        }

    except Exception:
        return {}


def modelo_cadastro_empresa():
    return {
        "nome": "",
        "nome_fantasia": "",
        "cnpj": "",
        "situacao_cadastral": "",
        "data_abertura": "",
        "porte": "",
        "natureza_juridica": "",
        "capital_social": "",
        "cnae_principal": "",
        "cnaes_secundarios": "",
        "cep": "",
        "logradouro": "",
        "numero": "",
        "complemento": "",
        "bairro": "",
        "municipio": "",
        "uf": "",
        "qsa": "",
        "email": "",
        "telefone": "",
        "dados_cnpj_json": "",
        "documento_nome": "",
        "documento_processado": False,
    }


def limpar_cadastro_session():
    for key in list(st.session_state.keys()):
        if key.startswith("cad_"):
            del st.session_state[key]

    st.session_state["cadastro_empresa"] = modelo_cadastro_empresa()


def aplicar_dados_no_session(dados):
    if "cadastro_empresa" not in st.session_state:
        st.session_state["cadastro_empresa"] = modelo_cadastro_empresa()

    cad = st.session_state["cadastro_empresa"]

    for chave, valor in dados.items():
        if valor not in [None, ""]:
            cad[chave] = valor

    for chave, valor in cad.items():
        widget_key = f"cad_{chave}"
        if widget_key not in st.session_state:
            if chave == "telefone":
                st.session_state[widget_key] = formatar_telefone(valor)
            else:
                st.session_state[widget_key] = "" if valor is None else str(valor)


def carregar_documento_cadastro(documento_empresa):
    nome_arquivo = getattr(documento_empresa, "name", "")

    cad_atual = st.session_state.get("cadastro_empresa") or modelo_cadastro_empresa()

    if cad_atual.get("documento_processado") and cad_atual.get("documento_nome") == nome_arquivo:
        return True

    dados_doc = extrair_dados_cartao_cnpj_pdf(documento_empresa)

    if dados_doc.get("cnpj"):
        dados_api = consultar_cnpj_publica_ws(dados_doc.get("cnpj"))

        if dados_api:
            for chave, valor in dados_api.items():
                if valor not in [None, ""]:
                    dados_doc[chave] = valor

    dados_doc["documento_nome"] = nome_arquivo
    dados_doc["documento_processado"] = True

    st.session_state["cadastro_empresa"] = modelo_cadastro_empresa()
    aplicar_dados_no_session(dados_doc)

    return bool(dados_doc.get("nome")) and bool(dados_doc.get("cnpj"))


def sincronizar_cadastro_para_dict():
    if "cadastro_empresa" not in st.session_state:
        st.session_state["cadastro_empresa"] = modelo_cadastro_empresa()

    cad = st.session_state["cadastro_empresa"]

    for chave in list(cad.keys()):
        widget_key = f"cad_{chave}"
        if widget_key in st.session_state:
            cad[chave] = st.session_state[widget_key]

    return cad


def validar_cadastro(cad, senha, confirmar, empresa_existente):
    obrigatorios = {
        "Razão Social": cad.get("nome"),
        "CNPJ": cad.get("cnpj"),
        "Nome Fantasia": cad.get("nome_fantasia"),
        "Situação Cadastral": cad.get("situacao_cadastral"),
        "Natureza Jurídica": cad.get("natureza_juridica"),
        "Capital Social": cad.get("capital_social"),
        "CEP": cad.get("cep"),
        "Logradouro": cad.get("logradouro"),
        "Bairro": cad.get("bairro"),
        "Município": cad.get("municipio"),
        "UF": cad.get("uf"),
        "E-mail": cad.get("email"),
        "Telefone": cad.get("telefone"),
        "Senha": senha,
        "Confirmar senha": confirmar,
    }

    faltantes = [campo for campo, valor in obrigatorios.items() if not texto_padrao(valor)]

    if faltantes:
        return False, "Campos obrigatórios pendentes: " + ", ".join(faltantes)

    if empresa_existente is not None and empresa_existente.get("senha_hash"):
        return False, "Este CNPJ já possui conta cadastrada."

    if senha != confirmar:
        return False, "As senhas não conferem."

    if not telefone_valido(cad.get("telefone")):
        return False, "Telefone inválido. Informe DDD + número. Exemplo: (61) 99987-8710."

    return True, ""


def criar_empresa(nome, cnpj, email, telefone, senha, dados_cadastrais=None):
    dados_cadastrais = dados_cadastrais or {}

    conn = conectar()
    cur = conn.cursor()

    cnpj_limpo = limpar_cnpj(cnpj)

    cur.execute("""
        SELECT id, senha_hash
        FROM empresas
        WHERE REPLACE(REPLACE(REPLACE(REPLACE(cnpj_cpf,'.',''),'/',''),'-',''),' ','') = ?
        LIMIT 1
    """, (cnpj_limpo,))

    existente = cur.fetchone()

    valores = {
        "nome": texto_padrao(nome),
        "nome_fantasia": texto_padrao(dados_cadastrais.get("nome_fantasia")),
        "cnpj_cpf": cnpj_limpo,
        "email": texto_padrao(email),
        "telefone": limpar_telefone(telefone),
        "senha_hash": hash_senha(senha),
        "situacao_cadastral": texto_padrao(dados_cadastrais.get("situacao_cadastral")),
        "data_abertura": texto_padrao(dados_cadastrais.get("data_abertura")),
        "porte": texto_padrao(dados_cadastrais.get("porte")),
        "natureza_juridica": texto_padrao(dados_cadastrais.get("natureza_juridica")),
        "capital_social": normalizar_capital_social(dados_cadastrais.get("capital_social")),
        "cnae_principal": texto_padrao(dados_cadastrais.get("cnae_principal")),
        "cnaes_secundarios": texto_padrao(dados_cadastrais.get("cnaes_secundarios")),
        "cep": texto_padrao(dados_cadastrais.get("cep")),
        "logradouro": texto_padrao(dados_cadastrais.get("logradouro")),
        "numero": texto_padrao(dados_cadastrais.get("numero")),
        "complemento": texto_padrao(dados_cadastrais.get("complemento")),
        "bairro": texto_padrao(dados_cadastrais.get("bairro")),
        "municipio": texto_padrao(dados_cadastrais.get("municipio")),
        "uf": texto_padrao(dados_cadastrais.get("uf")).upper(),
        "qsa": texto_padrao(dados_cadastrais.get("qsa")),
        "dados_cnpj_json": texto_padrao(dados_cadastrais.get("dados_cnpj_json")),
        "plano": "Teste",
        "status_assinatura": "Ativa",
        "periodo_assinatura": "7 dias grátis",
    }

    if existente:
        empresa_id, senha_atual = existente

        if senha_atual:
            conn.close()
            return False, "CNPJ já possui conta cadastrada.", None

        cur.execute("""
            UPDATE empresas
            SET nome = ?,
                nome_fantasia = ?,
                cnpj_cpf = ?,
                email = ?,
                telefone = ?,
                senha_hash = ?,
                situacao_cadastral = ?,
                data_abertura = ?,
                porte = ?,
                natureza_juridica = ?,
                capital_social = ?,
                cnae_principal = ?,
                cnaes_secundarios = ?,
                cep = ?,
                logradouro = ?,
                numero = ?,
                complemento = ?,
                bairro = ?,
                municipio = ?,
                uf = ?,
                qsa = ?,
                dados_cnpj_json = ?,
                plano = COALESCE(plano, ?),
                status_assinatura = 'Ativa',
                periodo_assinatura = COALESCE(periodo_assinatura, ?),
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            valores["nome"],
            valores["nome_fantasia"],
            valores["cnpj_cpf"],
            valores["email"],
            valores["telefone"],
            valores["senha_hash"],
            valores["situacao_cadastral"],
            valores["data_abertura"],
            valores["porte"],
            valores["natureza_juridica"],
            valores["capital_social"],
            valores["cnae_principal"],
            valores["cnaes_secundarios"],
            valores["cep"],
            valores["logradouro"],
            valores["numero"],
            valores["complemento"],
            valores["bairro"],
            valores["municipio"],
            valores["uf"],
            valores["qsa"],
            valores["dados_cnpj_json"],
            valores["plano"],
            valores["periodo_assinatura"],
            empresa_id,
        ))

        conn.commit()
        conn.close()
        return True, "Conta criada. Entrando na GOIA.", empresa_id

    cur.execute("""
        INSERT INTO empresas (
            nome,
            nome_fantasia,
            cnpj_cpf,
            email,
            telefone,
            senha_hash,
            situacao_cadastral,
            data_abertura,
            porte,
            natureza_juridica,
            capital_social,
            cnae_principal,
            cnaes_secundarios,
            cep,
            logradouro,
            numero,
            complemento,
            bairro,
            municipio,
            uf,
            qsa,
            dados_cnpj_json,
            plano,
            status_assinatura,
            periodo_assinatura
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        valores["nome"],
        valores["nome_fantasia"],
        valores["cnpj_cpf"],
        valores["email"],
        valores["telefone"],
        valores["senha_hash"],
        valores["situacao_cadastral"],
        valores["data_abertura"],
        valores["porte"],
        valores["natureza_juridica"],
        valores["capital_social"],
        valores["cnae_principal"],
        valores["cnaes_secundarios"],
        valores["cep"],
        valores["logradouro"],
        valores["numero"],
        valores["complemento"],
        valores["bairro"],
        valores["municipio"],
        valores["uf"],
        valores["qsa"],
        valores["dados_cnpj_json"],
        valores["plano"],
        valores["status_assinatura"],
        valores["periodo_assinatura"],
    ))

    empresa_id = cur.lastrowid

    conn.commit()
    conn.close()
    return True, "Conta criada. Entrando na GOIA.", empresa_id


def garantir_empresa_bootstrap():
    senha = os.environ.get("GOIA_BOOTSTRAP_PASSWORD", "").strip()

    if not senha:
        return

    cnpj = "28860122000177"
    nome = "GODS - PRODUTOS, SERVICOS & EVENTOS LTDA"
    email = os.environ.get("GOIA_BOOTSTRAP_EMAIL", "admin@gods.com.br").strip()
    telefone = os.environ.get("GOIA_BOOTSTRAP_TELEFONE", "61999878710").strip()

    dados = {
        "nome_fantasia": os.environ.get("GOIA_BOOTSTRAP_FANTASIA", "GODS").strip(),
    }

    criar_empresa(nome, cnpj, email, telefone, senha, dados)


def suspender_testes_expirados():
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE empresas
            SET status_assinatura = 'Suspensa',
                motivo_bloqueio = 'Teste grátis de 7 dias expirado'
            WHERE status_assinatura = 'Teste'
              AND data_fim_assinatura IS NOT NULL
              AND datetime(data_fim_assinatura) < datetime('now')
        """)
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def tela_login():
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {display:none;}
    .block-container {max-width:1100px; padding-top:55px;}
    .hero {
        background:linear-gradient(135deg,#050816,#172554);
        color:white; padding:46px; border-radius:28px;
        box-shadow:0 22px 60px rgba(15,23,42,.22);
        margin-bottom:26px;
    }
    .kicker {color:#2dd4bf; font-weight:800; letter-spacing:.18em; font-size:13px;}
    .title {font-size:42px; font-weight:900; line-height:1.08; margin-top:16px;}
    .text {color:#cbd5e1; font-size:17px; margin-top:18px;}
    .stTextInput input {
        background:#fff !important;
        border:2px solid #334155 !important;
        color:#0f172a !important;
        font-weight:700 !important;
    }
    .stButton button {
        background:#111827 !important;
        color:white !important;
        border-radius:10px !important;
        font-weight:800 !important;
    }
    </style>

    <div class="hero">
      <div class="kicker">GOIA FINANCE PLATFORM</div>
      <div class="title">Inteligência financeira para empresas document-driven.</div>
      <div class="text">Entre com o CNPJ da empresa ou crie sua conta para iniciar.</div>
    </div>
    """, unsafe_allow_html=True)

    aba_login, aba_cadastro = st.tabs(["Já tenho conta", "Criar conta"])

    with aba_login:
        st.subheader("Acessar sistema")

        with st.form("login"):
            cnpj = st.text_input("CNPJ")
            senha = st.text_input("Senha", type="password")
            acessar = st.form_submit_button("Acessar sistema")

        if acessar:
            empresa = buscar_empresa(cnpj, senha)

            if not empresa:
                st.error("CNPJ ou senha inválidos.")
                st.stop()

            st.session_state["logado"] = True
            st.session_state["empresa_id"] = empresa["id"]
            st.session_state["empresa_nome"] = empresa["nome"]
            st.rerun()

    with aba_cadastro:
        tela_cadastro_empresa()

    st.stop()


def tela_cadastro_empresa():
    st.subheader("Cadastrar empresa")
    st.caption("Anexe o Cartão CNPJ oficial. A GOIA preencherá os dados e manterá suas edições durante a revisão.")

    if "cadastro_empresa" not in st.session_state:
        st.session_state["cadastro_empresa"] = modelo_cadastro_empresa()

    col_upload, col_acao = st.columns([3, 1])

    with col_upload:
        documento_empresa = st.file_uploader(
            "Anexar Cartão CNPJ / documento oficial da empresa",
            type=["pdf"],
            key="documento_cadastro_empresa"
        )

    with col_acao:
        st.write("")
        st.write("")
        if st.button("Limpar cadastro", use_container_width=True):
            limpar_cadastro_session()
            st.rerun()

    if not documento_empresa and not st.session_state["cadastro_empresa"].get("documento_processado"):
        st.warning("Anexe o Cartão CNPJ para liberar o cadastro.")

    if documento_empresa:
        valido = carregar_documento_cadastro(documento_empresa)

        if valido:
            st.success(f"Documento lido e cadastro enriquecido pela API CNPJ: {documento_empresa.name}")
        else:
            st.error("Documento anexado, mas não foi possível identificar Razão Social e CNPJ. Envie o Cartão CNPJ oficial em PDF.")

    cad = sincronizar_cadastro_para_dict()

    documento_valido = bool(texto_padrao(cad.get("nome"))) and bool(texto_padrao(cad.get("cnpj")))

    empresa_existente = None
    if documento_valido:
        empresa_existente = empresa_existe_por_cnpj(cad.get("cnpj"))

        if empresa_existente and empresa_existente.get("senha_hash"):
            st.warning("Este CNPJ já possui conta cadastrada na GOIA. Use a aba 'Já tenho conta' para acessar.")
        elif empresa_existente and not empresa_existente.get("senha_hash"):
            st.info("Este CNPJ já existe na base, mas ainda não possui senha. Complete o cadastro para ativar o acesso.")

    with st.container(border=True):
        st.markdown("### Dados empresariais identificados")

        st.text_input("CNPJ", key="cad_cnpj", disabled=True)
        st.text_input("Razão Social", key="cad_nome", disabled=not documento_valido)

        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Nome Fantasia", key="cad_nome_fantasia")
            st.text_input("Situação Cadastral", key="cad_situacao_cadastral")
            st.text_input("Data de Abertura", key="cad_data_abertura")
            st.text_input("Porte", key="cad_porte")
        with c2:
            st.text_input("Natureza Jurídica", key="cad_natureza_juridica")
            st.text_input("Capital Social", key="cad_capital_social")
            st.text_input("CNAE Principal", key="cad_cnae_principal")

        st.text_area("CNAEs Secundários", key="cad_cnaes_secundarios", height=120)

        st.markdown("### Endereço")

        e1, e2, e3 = st.columns([1, 2, 1])
        with e1:
            st.text_input("CEP", key="cad_cep")
        with e2:
            st.text_input("Logradouro", key="cad_logradouro")
        with e3:
            st.text_input("Número", key="cad_numero")

        e4, e5, e6, e7 = st.columns([2, 2, 2, 1])
        with e4:
            st.text_input("Complemento", key="cad_complemento")
        with e5:
            st.text_input("Bairro", key="cad_bairro")
        with e6:
            st.text_input("Município", key="cad_municipio")
        with e7:
            st.text_input("UF", key="cad_uf")

        st.text_area("Sócios / QSA", key="cad_qsa", height=120)

        st.markdown("### Acesso")

        a1, a2 = st.columns(2)
        with a1:
            st.text_input("E-mail de acesso", key="cad_email")
        with a2:
            st.text_input(
                "Telefone / WhatsApp",
                key="cad_telefone",
                help="Digite DDD + número. Exemplo: (61) 99987-8710"
            )

        senha = st.text_input("Senha", type="password", key="cad_senha")
        confirmar = st.text_input("Confirmar senha", type="password", key="cad_confirmar")

        cad = sincronizar_cadastro_para_dict()

        valido, mensagem = validar_cadastro(cad, senha, confirmar, empresa_existente)

        if documento_valido and not valido:
            st.warning(mensagem)

        criar = st.button(
            "Criar conta",
            disabled=bool((not documento_valido) or (not valido)),
            use_container_width=True
        )

    if criar:
        dados_cadastrais = {
            "nome_fantasia": cad.get("nome_fantasia"),
            "situacao_cadastral": cad.get("situacao_cadastral"),
            "data_abertura": cad.get("data_abertura"),
            "porte": cad.get("porte"),
            "natureza_juridica": cad.get("natureza_juridica"),
            "capital_social": cad.get("capital_social"),
            "cnae_principal": cad.get("cnae_principal"),
            "cnaes_secundarios": cad.get("cnaes_secundarios"),
            "cep": cad.get("cep"),
            "logradouro": cad.get("logradouro"),
            "numero": cad.get("numero"),
            "complemento": cad.get("complemento"),
            "bairro": cad.get("bairro"),
            "municipio": cad.get("municipio"),
            "uf": cad.get("uf"),
            "qsa": cad.get("qsa"),
            "dados_cnpj_json": cad.get("dados_cnpj_json"),
        }

        ok, msg, empresa_id = criar_empresa(
            cad.get("nome"),
            cad.get("cnpj"),
            cad.get("email"),
            cad.get("telefone"),
            senha,
            dados_cadastrais
        )

        if ok:
            nome_empresa = cad.get("nome")
            limpar_cadastro_session()
            st.session_state["logado"] = True
            st.session_state["empresa_id"] = empresa_id
            st.session_state["empresa_nome"] = nome_empresa
            st.success(msg)
            st.rerun()
        else:
            st.warning(msg)


inicializar_schema_goia()
suspender_testes_expirados()
garantir_empresa_bootstrap()

if not st.session_state.get("logado") or not st.session_state.get("empresa_id"):
    tela_login()
    st.stop()


EMPRESA_ID = st.session_state.get("empresa_id")


def carregar_movimentacoes():
    conn = conectar()

    try:
        receber = pd.read_sql_query("""
            SELECT data_vencimento AS data, 'Receber' AS tipo, descricao, categoria, valor, status
            FROM contas_receber
            WHERE empresa_id = ?
        """, conn, params=(EMPRESA_ID,))
    except Exception:
        receber = pd.DataFrame(columns=["data", "tipo", "descricao", "categoria", "valor", "status"])

    try:
        pagar = pd.read_sql_query("""
            SELECT data_vencimento AS data, 'Pagar' AS tipo, descricao, categoria, -valor AS valor, status
            FROM contas_pagar
            WHERE empresa_id = ?
        """, conn, params=(EMPRESA_ID,))
    except Exception:
        pagar = pd.DataFrame(columns=["data", "tipo", "descricao", "categoria", "valor", "status"])

    conn.close()
    return pd.concat([receber, pagar], ignore_index=True)


df = carregar_movimentacoes()

recebimentos = df[df["tipo"] == "Receber"]["valor"].sum() if not df.empty else 0
pagamentos = abs(df[df["tipo"] == "Pagar"]["valor"].sum()) if not df.empty else 0
saldo = recebimentos - pagamentos


def contar_tabela(nome_tabela, where="empresa_id = ?", params=None):
    conn = conectar()
    cur = conn.cursor()
    params = params or (EMPRESA_ID,)

    try:
        cur.execute(f"SELECT COUNT(*) FROM {nome_tabela} WHERE {where}", params)
        valor = cur.fetchone()[0] or 0
    except Exception:
        valor = 0

    conn.close()
    return valor


def somar_tabela(nome_tabela, coluna, where="empresa_id = ?", params=None):
    conn = conectar()
    cur = conn.cursor()
    params = params or (EMPRESA_ID,)

    try:
        cur.execute(f"SELECT COALESCE(SUM({coluna}), 0) FROM {nome_tabela} WHERE {where}", params)
        valor = cur.fetchone()[0] or 0
    except Exception:
        valor = 0

    conn.close()
    return valor


receber_aberto = somar_tabela(
    "contas_receber",
    "valor",
    "empresa_id = ? AND COALESCE(status, 'Pendente') NOT IN ('Baixada', 'Baixado', 'Liquidado')"
)

pagar_aberto = somar_tabela(
    "contas_pagar",
    "valor",
    "empresa_id = ? AND COALESCE(status, 'Pendente') NOT IN ('Baixada', 'Baixado', 'Liquidado')"
)

saldo_projetado = receber_aberto - pagar_aberto

documentos_importados = contar_tabela("documentos")

processos_abertos = contar_tabela(
    "processos_documentais",
    "empresa_id = ? AND COALESCE(status, 'Aberto') <> 'Concluído'"
)

pendencias_abertas = contar_tabela(
    "processo_pendencias",
    "empresa_id = ? AND COALESCE(status, 'Pendente') = 'Pendente'"
)

movimentos_nao_conciliados = contar_tabela(
    "movimentos_bancarios",
    "empresa_id = ? AND COALESCE(conciliado, 0) = 0"
)

st.sidebar.markdown("## GOIA")
st.sidebar.caption(st.session_state.get("empresa_nome"))

if st.sidebar.button("Sair"):
    st.session_state.clear()
    st.rerun()

st.sidebar.page_link("app.py", label="Dashboard", icon="🏠")
st.sidebar.page_link("pages/1_Importar_Documento.py", label="Importar Documento", icon="📄")
st.sidebar.page_link("pages/9_Clientes.py", label="Clientes", icon="👥")
st.sidebar.page_link("pages/10_Fornecedores.py", label="Fornecedores", icon="🏭")
st.sidebar.page_link("pages/2_Contas_a_Receber.py", label="Contas a Receber", icon="💰")
st.sidebar.page_link("pages/3_Contas_a_Pagar.py", label="Contas a Pagar", icon="💸")
st.sidebar.page_link("pages/8_Movimentos_Bancarios.py", label="Movimentos Bancários", icon="🏦")
st.sidebar.page_link("pages/8_Conciliacao_Bancaria.py", label="Conciliação Bancária", icon="⚖️")
st.sidebar.page_link("pages/99_Diagnostico_Banco.py", label="Diagnóstico Banco", icon="🧪")

hero(
    "Dashboard Executivo",
    f"Empresa ativa: {st.session_state.get('empresa_nome')} | Visao consolidada de caixa, documentos, pendencias e conciliacao.",
    icone="GOIA"
)

section_title(
    "Resumo financeiro",
    "Indicadores consolidados de recebimentos, pagamentos e saldo projetado."
)

k1, k2, k3 = st.columns(3)

with k1:
    kpi_card("Receber em aberto", moeda(receber_aberto), "Titulos ainda nao baixados", "positivo")

with k2:
    kpi_card("Pagar em aberto", moeda(pagar_aberto), "Obrigacoes financeiras pendentes", "alerta")

with k3:
    status_saldo = "positivo" if saldo_projetado >= 0 else "negativo"
    kpi_card("Saldo projetado", moeda(saldo_projetado), "Receber aberto menos pagar aberto", status_saldo)

section_title(
    "Governanca operacional",
    "Controle de documentos, processos, pendencias e conciliacoes."
)

g1, g2, g3, g4 = st.columns(4)

with g1:
    kpi_card("Documentos", documentos_importados, "Documentos importados", "neutro")

with g2:
    kpi_card("Processos abertos", processos_abertos, "Fluxos documentais ativos", "alerta" if processos_abertos else "positivo")

with g3:
    kpi_card("Pendencias", pendencias_abertas, "Itens aguardando evidencias", "alerta" if pendencias_abertas else "positivo")

with g4:
    kpi_card("Nao conciliados", movimentos_nao_conciliados, "Movimentos bancarios pendentes", "alerta" if movimentos_nao_conciliados else "positivo")

section_title(
    "Movimentacoes financeiras",
    "Ultimos registros financeiros consolidados entre contas a receber e contas a pagar."
)

if df.empty:
    st.info("Nenhuma movimentacao encontrada para esta empresa.")
else:
    st.dataframe(df, use_container_width=True, hide_index=True)