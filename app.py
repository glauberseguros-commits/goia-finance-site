import sqlite3
import json
import urllib.request
import urllib.error
import os
import hashlib
import re
from pathlib import Path
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

def limpar_doc(v):
    return "".join(filter(str.isdigit, v or ""))

def hash_senha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def moeda(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def preparar_banco():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL
    )
    """)

    cur.execute("PRAGMA table_info(empresas)")
    cols = [c[1] for c in cur.fetchall()]

    def add_col(nome, tipo):
        if nome not in cols:
            cur.execute(f"ALTER TABLE empresas ADD COLUMN {nome} {tipo}")

    add_col("cnpj_cpf", "TEXT")
    add_col("email", "TEXT")
    add_col("telefone", "TEXT")
    add_col("senha_hash", "TEXT")
    add_col("plano", "TEXT DEFAULT 'Teste'")
    add_col("status_assinatura", "TEXT DEFAULT 'Ativa'")
    add_col("criado_em", "TEXT DEFAULT CURRENT_TIMESTAMP")

    # Normaliza CNPJs já existentes
    cur.execute("SELECT id, cnpj_cpf FROM empresas")
    for empresa_id, cnpj in cur.fetchall():
        if cnpj:
            cnpj_limpo = ''.join(filter(str.isdigit, cnpj))
            if cnpj_limpo:
                cur.execute(
                    "UPDATE empresas SET cnpj_cpf = ? WHERE id = ?",
                    (cnpj_limpo, empresa_id)
                )

    # Impede duas empresas com o mesmo CNPJ preenchido
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_empresas_cnpj_cpf_unico
    ON empresas(cnpj_cpf)
    WHERE cnpj_cpf IS NOT NULL AND cnpj_cpf <> ''
    """)

    conn.commit()
    conn.close()


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
    conn.row_factory = sqlite3.Row
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
    return dict(row) if row else None

def criar_empresa(nome, cnpj, email, telefone, senha):
    conn = conectar()
    cur = conn.cursor()

    cnpj_limpo = limpar_cnpj(cnpj)

    cur.execute("""
    SELECT id, senha_hash
    FROM empresas
    WHERE REPLACE(REPLACE(REPLACE(REPLACE(cnpj_cpf,'.',''),'/',''),'-',''),' ','') = ?
    """, (cnpj_limpo,))

    existente = cur.fetchone()

    if existente:
        empresa_id, senha_atual = existente

        if senha_atual:
            conn.close()
            return False, "CNPJ já possui conta cadastrada.", None

        cur.execute("""
        UPDATE empresas
        SET nome = ?, cnpj_cpf = ?, email = ?, telefone = ?, senha_hash = ?,
            status_assinatura = COALESCE(status_assinatura, 'Ativa')
        WHERE id = ?
        """, (nome, cnpj_limpo, email, limpar_telefone(telefone), hash_senha(senha), empresa_id))

        conn.commit()
        conn.close()
        return True, "Conta criada. Entrando na GOIA.", empresa_id

    cur.execute("""
    INSERT INTO empresas (
        nome, cnpj_cpf, email, telefone, senha_hash, plano, status_assinatura
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        nome, cnpj_limpo, email, limpar_telefone(telefone), hash_senha(senha), "Teste", "Ativa"
    ))

    empresa_id = cur.lastrowid

    conn.commit()
    conn.close()
    return True, "Conta criada. Entrando na GOIA.", empresa_id


def formatar_cnpj(valor):
    numeros = re.sub(r"\D", "", valor or "")
    if len(numeros) == 14:
        return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"
    return valor or ""

def extrair_dados_cartao_cnpj_pdf(arquivo):
    dados = {"nome": "", "cnpj": "", "email": "", "telefone": ""}

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

    email = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", texto)
    if email:
        dados["email"] = email.group()

    telefone = re.search(r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}", texto)
    if telefone:
        dados["telefone"] = telefone.group()

    return dados



def garantir_enriquecimento_cadastral():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            nome TEXT,
            cnpj_cpf TEXT,
            email TEXT,
            telefone TEXT,
            endereco TEXT,
            cidade TEXT,
            uf TEXT,
            cep TEXT,
            status TEXT DEFAULT 'Ativo',
            origem_cadastro TEXT DEFAULT 'DOCUMENTO',
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS fornecedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            nome TEXT,
            cnpj TEXT,
            cnpj_cpf TEXT,
            email TEXT,
            telefone TEXT,
            endereco TEXT,
            cidade TEXT,
            uf TEXT,
            cep TEXT,
            categoria_padrao TEXT,
            tipo_padrao TEXT,
            status TEXT DEFAULT 'Ativo',
            origem_cadastro TEXT DEFAULT 'DOCUMENTO',
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    campos_por_tabela = {
        "clientes": [
            ("empresa_id", "INTEGER"),
            ("nome", "TEXT"),
            ("cnpj_cpf", "TEXT"),
            ("email", "TEXT"),
            ("telefone", "TEXT"),
            ("endereco", "TEXT"),
            ("cidade", "TEXT"),
            ("uf", "TEXT"),
            ("cep", "TEXT"),
            ("status", "TEXT DEFAULT 'Ativo'"),
            ("origem_cadastro", "TEXT DEFAULT 'DOCUMENTO'"),
            ("nome_fantasia", "TEXT"),
            ("cnae_principal", "TEXT"),
            ("natureza_juridica", "TEXT"),
            ("capital_social", "REAL"),
            ("situacao_cadastral", "TEXT")
        ],
        "fornecedores": [
            ("empresa_id", "INTEGER"),
            ("nome", "TEXT"),
            ("cnpj", "TEXT"),
            ("cnpj_cpf", "TEXT"),
            ("email", "TEXT"),
            ("telefone", "TEXT"),
            ("endereco", "TEXT"),
            ("cidade", "TEXT"),
            ("uf", "TEXT"),
            ("cep", "TEXT"),
            ("categoria_padrao", "TEXT"),
            ("tipo_padrao", "TEXT"),
            ("status", "TEXT DEFAULT 'Ativo'"),
            ("origem_cadastro", "TEXT DEFAULT 'DOCUMENTO'"),
            ("nome_fantasia", "TEXT"),
            ("cnae_principal", "TEXT"),
            ("natureza_juridica", "TEXT"),
            ("capital_social", "REAL"),
            ("situacao_cadastral", "TEXT")
        ]
    }

    for tabela, campos in campos_por_tabela.items():
        cur.execute(f"PRAGMA table_info({tabela})")
        existentes = [c[1] for c in cur.fetchall()]

        for campo, tipo in campos:
            if campo not in existentes:
                cur.execute(f"ALTER TABLE {tabela} ADD COLUMN {campo} {tipo}")

    conn.commit()
    conn.close()



def criar_pendencia_automatica(
    empresa_id,
    processo_id,
    descricao,
    tipo_evidencia="Evidencia documental",
    documento_id=None,
    proxima_acao=None
):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id
        FROM processo_pendencias
        WHERE empresa_id = ?
          AND processo_id = ?
          AND descricao = ?
          AND COALESCE(status, 'Pendente') = 'Pendente'
    """, (
        empresa_id,
        processo_id,
        descricao
    ))

    existente = cur.fetchone()

    if existente:
        conn.close()
        return existente[0]

    cur.execute("""
        INSERT INTO processo_pendencias (
            empresa_id,
            processo_id,
            descricao,
            tipo_evidencia,
            documento_id,
            proxima_acao,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, 'Pendente')
    """, (
        empresa_id,
        processo_id,
        descricao,
        tipo_evidencia,
        documento_id,
        proxima_acao
    ))

    pendencia_id = cur.lastrowid

    conn.commit()
    conn.close()

    return pendencia_id



def garantir_motor_encerramento():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS contas_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            fornecedor_id INTEGER,
            processo_id INTEGER,
            documento_id INTEGER,
            descricao TEXT,
            categoria TEXT,
            valor REAL DEFAULT 0,
            data_emissao TEXT,
            data_vencimento TEXT,
            data_baixa TEXT,
            valor_baixado REAL DEFAULT 0,
            forma_pagamento TEXT,
            observacao_baixa TEXT,
            status TEXT DEFAULT 'Pendente',
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS processo_pendencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            processo_id INTEGER,
            documento_id INTEGER,
            descricao TEXT,
            tipo_evidencia TEXT,
            proxima_acao TEXT,
            status TEXT DEFAULT 'Pendente',
            resolvido_em TEXT,
            resolvido_por TEXT,
            evidencia_resolucao_id INTEGER,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    garantias = {
        "contas_pagar": [
            ("empresa_id", "INTEGER"),
            ("fornecedor_id", "INTEGER"),
            ("processo_id", "INTEGER"),
            ("documento_id", "INTEGER"),
            ("descricao", "TEXT"),
            ("categoria", "TEXT"),
            ("valor", "REAL DEFAULT 0"),
            ("data_emissao", "TEXT"),
            ("data_vencimento", "TEXT"),
            ("data_baixa", "TEXT"),
            ("valor_baixado", "REAL DEFAULT 0"),
            ("forma_pagamento", "TEXT"),
            ("observacao_baixa", "TEXT"),
            ("status", "TEXT DEFAULT 'Pendente'"),
            ("criado_em", "TEXT DEFAULT CURRENT_TIMESTAMP")
        ],
        "processo_pendencias": [
            ("empresa_id", "INTEGER"),
            ("processo_id", "INTEGER"),
            ("documento_id", "INTEGER"),
            ("descricao", "TEXT"),
            ("tipo_evidencia", "TEXT"),
            ("proxima_acao", "TEXT"),
            ("status", "TEXT DEFAULT 'Pendente'"),
            ("resolvido_em", "TEXT"),
            ("resolvido_por", "TEXT"),
            ("evidencia_resolucao_id", "INTEGER"),
            ("criado_em", "TEXT DEFAULT CURRENT_TIMESTAMP")
        ]
    }

    for tabela, campos in garantias.items():
        cur.execute(f"PRAGMA table_info({tabela})")
        existentes = [c[1] for c in cur.fetchall()]

        for campo, tipo in campos:
            if campo not in existentes:
                cur.execute(f"ALTER TABLE {tabela} ADD COLUMN {campo} {tipo}")

    conn.commit()
    conn.close()



def garantir_schema_documental():
    """
    Garante tabelas documentais mínimas no banco persistente.
    Necessário no Render quando /data/gofinance.db existe, mas ainda não possui estrutura operacional.
    """
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            processo_id INTEGER,
            cliente_id INTEGER,
            fornecedor_id INTEGER,
            nome_arquivo TEXT,
            tipo_documento TEXT,
            classificacao TEXT,
            direcao TEXT,
            origem TEXT,
            conteudo_texto TEXT,
            chave_acesso_nfe TEXT,
            numero_nfe TEXT,
            serie_nfe TEXT,
            cnpj_emitente TEXT,
            nome_emitente TEXT,
            cnpj_destinatario TEXT,
            nome_destinatario TEXT,
            contraparte_nome TEXT,
            contraparte_documento TEXT,
            data_documento TEXT,
            data_emissao TEXT,
            data_vencimento TEXT,
            valor_total REAL DEFAULT 0,
            valor REAL DEFAULT 0,
            status TEXT DEFAULT 'Importado',
            status_processamento TEXT DEFAULT 'Processado',
            erro_processamento TEXT,
            processado_em TEXT,
            hash_arquivo TEXT,
            caminho_arquivo TEXT,
            extensao TEXT,
            tamanho_bytes INTEGER,
            observacao TEXT,
            diagnostico_tecnico TEXT,
            dados_extraidos_json TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS processos_documentais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            titulo TEXT,
            descricao TEXT,
            tipo_processo TEXT,
            status TEXT DEFAULT 'Aberto',
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS processo_documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            processo_id INTEGER,
            documento_id INTEGER,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS evidencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            processo_id INTEGER,
            documento_id INTEGER,
            tipo_evidencia TEXT,
            descricao TEXT,
            valor TEXT,
            status TEXT DEFAULT 'Ativa',
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS processo_evidencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            processo_id INTEGER,
            documento_id INTEGER,
            evidencia_id INTEGER,
            tipo_evidencia TEXT,
            descricao TEXT,
            valor TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    garantias = {
        "documentos": [
            ("empresa_id", "INTEGER"),
            ("processo_id", "INTEGER"),
            ("cliente_id", "INTEGER"),
            ("fornecedor_id", "INTEGER"),
            ("nome_arquivo", "TEXT"),
            ("tipo_documento", "TEXT"),
            ("classificacao", "TEXT"),
            ("direcao", "TEXT"),
            ("origem", "TEXT"),
            ("conteudo_texto", "TEXT"),
            ("chave_acesso_nfe", "TEXT"),
            ("numero_nfe", "TEXT"),
            ("serie_nfe", "TEXT"),
            ("cnpj_emitente", "TEXT"),
            ("nome_emitente", "TEXT"),
            ("cnpj_destinatario", "TEXT"),
            ("nome_destinatario", "TEXT"),
            ("contraparte_nome", "TEXT"),
            ("contraparte_documento", "TEXT"),
            ("data_documento", "TEXT"),
            ("data_emissao", "TEXT"),
            ("data_vencimento", "TEXT"),
            ("valor_total", "REAL DEFAULT 0"),
            ("valor", "REAL DEFAULT 0"),
            ("status", "TEXT DEFAULT 'Importado'"),
            ("status_processamento", "TEXT DEFAULT 'Processado'"),
            ("erro_processamento", "TEXT"),
            ("processado_em", "TEXT"),
            ("hash_arquivo", "TEXT"),
            ("caminho_arquivo", "TEXT"),
            ("extensao", "TEXT"),
            ("tamanho_bytes", "INTEGER"),
            ("observacao", "TEXT"),
            ("diagnostico_tecnico", "TEXT"),
            ("dados_extraidos_json", "TEXT"),
            ("criado_em", "TEXT DEFAULT CURRENT_TIMESTAMP")
        ],
        "processos_documentais": [
            ("empresa_id", "INTEGER"),
            ("titulo", "TEXT"),
            ("descricao", "TEXT"),
            ("tipo_processo", "TEXT"),
            ("status", "TEXT DEFAULT 'Aberto'"),
            ("criado_em", "TEXT DEFAULT CURRENT_TIMESTAMP"),
            ("atualizado_em", "TEXT")
        ],
        "processo_documentos": [
            ("empresa_id", "INTEGER"),
            ("processo_id", "INTEGER"),
            ("documento_id", "INTEGER"),
            ("criado_em", "TEXT DEFAULT CURRENT_TIMESTAMP")
        ],
        "evidencias": [
            ("empresa_id", "INTEGER"),
            ("processo_id", "INTEGER"),
            ("documento_id", "INTEGER"),
            ("tipo_evidencia", "TEXT"),
            ("descricao", "TEXT"),
            ("valor", "TEXT"),
            ("status", "TEXT DEFAULT 'Ativa'"),
            ("criado_em", "TEXT DEFAULT CURRENT_TIMESTAMP")
        ],
        "processo_evidencias": [
            ("empresa_id", "INTEGER"),
            ("processo_id", "INTEGER"),
            ("documento_id", "INTEGER"),
            ("evidencia_id", "INTEGER"),
            ("tipo_evidencia", "TEXT"),
            ("descricao", "TEXT"),
            ("valor", "TEXT"),
            ("criado_em", "TEXT DEFAULT CURRENT_TIMESTAMP")
        ]
    }

    for tabela, campos in garantias.items():
        cur.execute(f"PRAGMA table_info({tabela})")
        existentes = [c[1] for c in cur.fetchall()]

        for campo, tipo in campos:
            if campo not in existentes:
                cur.execute(f"ALTER TABLE {tabela} ADD COLUMN {campo} {tipo}")

    conn.commit()
    conn.close()



def garantir_empresa_bootstrap():
    """
    Cria ou atualiza a empresa GODS no banco persistente do Render usando senha via variável de ambiente.
    Não deixa senha hardcoded no código.
    """
    senha = os.environ.get("GOIA_BOOTSTRAP_PASSWORD", "").strip()

    if not senha:
        return

    cnpj = "28860122000177"
    nome = "GODS - PRODUTOS, SERVICOS & EVENTOS LTDA"
    email = os.environ.get("GOIA_BOOTSTRAP_EMAIL", "admin@gods.com.br").strip()
    telefone = os.environ.get("GOIA_BOOTSTRAP_TELEFONE", "61999878710").strip()

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cnpj_cpf TEXT,
            email TEXT,
            telefone TEXT,
            senha_hash TEXT,
            plano TEXT DEFAULT 'Teste',
            status_assinatura TEXT DEFAULT 'Ativa',
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("PRAGMA table_info(empresas)")
    existentes = [c[1] for c in cur.fetchall()]

    campos = [
        ("cnpj_cpf", "TEXT"),
        ("email", "TEXT"),
        ("telefone", "TEXT"),
        ("senha_hash", "TEXT"),
        ("plano", "TEXT DEFAULT 'Teste'"),
        ("status_assinatura", "TEXT DEFAULT 'Ativa'"),
        ("criado_em", "TEXT DEFAULT CURRENT_TIMESTAMP")
    ]

    for campo, tipo in campos:
        if campo not in existentes:
            cur.execute(f"ALTER TABLE empresas ADD COLUMN {campo} {tipo}")

    senha_hash = hash_senha(senha)

    cur.execute("""
        SELECT id
        FROM empresas
        WHERE REPLACE(REPLACE(REPLACE(REPLACE(cnpj_cpf,'.',''),'/',''),'-',''),' ','') = ?
        LIMIT 1
    """, (cnpj,))

    row = cur.fetchone()

    if row:
        empresa_id = row[0]
        cur.execute("""
            UPDATE empresas
            SET nome = ?,
                cnpj_cpf = ?,
                email = ?,
                telefone = ?,
                senha_hash = ?,
                plano = COALESCE(plano, 'Teste'),
                status_assinatura = 'Ativa'
            WHERE id = ?
        """, (nome, cnpj, email, telefone, senha_hash, empresa_id))
    else:
        cur.execute("""
            INSERT INTO empresas (
                nome, cnpj_cpf, email, telefone, senha_hash, plano, status_assinatura
            )
            VALUES (?, ?, ?, ?, ?, 'Teste', 'Ativa')
        """, (nome, cnpj, email, telefone, senha_hash))

    conn.commit()
    conn.close()




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
            data = json.loads(resp.read().decode("utf-8"))

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
        }

    except Exception:
        return {}


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
        st.subheader("Cadastrar empresa")

        st.caption("Primeiro anexe o Cartão CNPJ oficial. A GOIA preencherá Razão Social e CNPJ a partir do documento.")

        documento_empresa = st.file_uploader(
            "Anexar Cartão CNPJ / documento oficial da empresa",
            type=["pdf"],
            key="documento_cadastro_empresa"
        )

        dados_doc = {"nome": "", "cnpj": "", "email": "", "telefone": ""}

        if not documento_empresa:
            st.warning("Anexe o Cartão CNPJ para liberar o cadastro.")
        else:
            dados_doc = extrair_dados_cartao_cnpj_pdf(documento_empresa)

            if dados_doc.get("cnpj"):
                dados_api = consultar_cnpj_publica_ws(dados_doc.get("cnpj"))

                if dados_api:
                    for chave, valor in dados_api.items():
                        if valor not in [None, ""]:
                            dados_doc[chave] = valor

            if dados_doc.get("nome") and dados_doc.get("cnpj"):
                st.success(f"Documento lido e cadastro enriquecido pela API CNPJ: {documento_empresa.name}")
            else:
                st.error("Documento anexado, mas não foi possível identificar Razão Social e CNPJ. Envie o Cartão CNPJ oficial em PDF.")

        documento_valido = bool(dados_doc.get("nome")) and bool(dados_doc.get("cnpj"))

        nome_oficial = dados_doc.get("nome", "")
        cnpj_oficial = dados_doc.get("cnpj", "")

        empresa_existente = None
        if documento_valido:
            empresa_existente = empresa_existe_por_cnpj(cnpj_oficial)

            if empresa_existente and empresa_existente.get("senha_hash"):
                st.warning(
                    "Este CNPJ já possui conta cadastrada na GOIA. "
                    "Use a aba 'Já tenho conta' para acessar."
                )
            elif empresa_existente and not empresa_existente.get("senha_hash"):
                st.info(
                    "Este CNPJ já existe na base, mas ainda não possui senha. "
                    "Complete o cadastro para ativar o acesso."
                )

        with st.container(border=True):
            st.markdown("### Dados empresariais identificados")

            cnpj_oficial = st.text_input(
                "CNPJ",
                value=cnpj_oficial,
                disabled=True
            )

            nome_oficial = st.text_input(
                "Razão Social",
                value=nome_oficial,
                disabled=not documento_valido
            )

            nome_fantasia = st.text_input("Nome Fantasia", value=(dados_doc.get("nome_fantasia") or ""))
            situacao_cadastral = st.text_input("Situação Cadastral", value=(dados_doc.get("situacao_cadastral") or dados_doc.get("situacao") or ""))
            data_abertura = st.text_input("Data de Abertura", value=(dados_doc.get("data_abertura") or dados_doc.get("abertura") or ""))
            porte = st.text_input("Porte", value=(dados_doc.get("porte") or ""))
            natureza_juridica = st.text_input("Natureza Jurídica", value=(dados_doc.get("natureza_juridica") or ""))
            capital_social = st.text_input("Capital Social", value=str(dados_doc.get("capital_social") or ""))

            cnae_principal = st.text_input("CNAE Principal", value=(dados_doc.get("cnae_principal") or dados_doc.get("cnae") or ""))
            cnaes_secundarios = st.text_area("CNAEs Secundários", value=str(dados_doc.get("cnaes_secundarios") or ""))

            st.markdown("### Endereço")
            cep = st.text_input("CEP", value=(dados_doc.get("cep") or ""))
            logradouro = st.text_input("Logradouro", value=(dados_doc.get("logradouro") or dados_doc.get("endereco") or ""))
            numero = st.text_input("Número", value=(dados_doc.get("numero") or ""))
            complemento = st.text_input("Complemento", value=(dados_doc.get("complemento") or ""))
            bairro = st.text_input("Bairro", value=(dados_doc.get("bairro") or ""))
            municipio = st.text_input("Município", value=(dados_doc.get("municipio") or dados_doc.get("cidade") or ""))
            uf = st.text_input("UF", value=(dados_doc.get("uf") or ""))

            qsa = st.text_area("Sócios / QSA", value=str(dados_doc.get("qsa") or dados_doc.get("socios") or ""))

            st.markdown("### Acesso")
            email = st.text_input("E-mail de acesso", value=(dados_doc.get("email") or ""))
            telefone = st.text_input(
                "Telefone / WhatsApp",
                value=formatar_telefone(dados_doc.get("telefone") or ""),
                help="Digite DDD + número. Exemplo: (61) 99987-8710"
            )
            senha = st.text_input("Senha", type="password")
            confirmar = st.text_input("Confirmar senha", type="password")

            bloquear_cadastro = False

            if not documento_valido:
                bloquear_cadastro = True

            if empresa_existente is not None and bool(empresa_existente.get("senha_hash")):
                bloquear_cadastro = True

            campos_obrigatorios_ok = all([
                nome_oficial.strip(),
                cnpj_oficial.strip(),
                nome_fantasia.strip(),
                situacao_cadastral.strip(),
                natureza_juridica.strip(),
                capital_social.strip(),
                cep.strip(),
                logradouro.strip(),
                bairro.strip(),
                municipio.strip(),
                uf.strip(),
                email.strip(),
                telefone.strip(),
                senha.strip(),
                confirmar.strip(),
            ])

            if documento_valido and not campos_obrigatorios_ok:
                st.warning("Preencha todos os campos obrigatórios antes de criar a conta.")

            criar = st.button(
                "Criar conta",
                disabled=bool(bloquear_cadastro or not campos_obrigatorios_ok)
            )

        if criar:
            if not documento_valido:
                st.error("Cadastro bloqueado: anexe o Cartão CNPJ oficial.")
            elif empresa_existente is not None and empresa_existente.get("senha_hash"):
                st.error("Cadastro bloqueado: este CNPJ já possui conta cadastrada.")
            elif senha != confirmar:
                st.error("As senhas não conferem.")
            elif not nome_oficial.strip() or not cnpj_oficial.strip():
                st.error("Razão Social e CNPJ são obrigatórios.")
            elif not nome_fantasia.strip() or not situacao_cadastral.strip() or not natureza_juridica.strip() or not capital_social.strip():
                st.error("Nome Fantasia, Situação Cadastral, Natureza Jurídica e Capital Social são obrigatórios.")
            elif not cep.strip() or not logradouro.strip() or not bairro.strip() or not municipio.strip() or not uf.strip():
                st.error("Endereço completo é obrigatório.")
            elif not email.strip() or not telefone.strip() or not senha:
                st.error("Informe e-mail, telefone e senha.")
            elif not telefone_valido(telefone):
                st.error("Telefone inválido. Informe DDD + número, exemplo: (61) 99987-8710.")
            else:
                dados_cadastrais = {
                    "nome_fantasia": nome_fantasia,
                    "situacao_cadastral": situacao_cadastral,
                    "data_abertura": data_abertura,
                    "porte": porte,
                    "natureza_juridica": natureza_juridica,
                    "capital_social": capital_social.replace(".", "").replace(",", ".") if capital_social else 0,
                    "cnae_principal": cnae_principal,
                    "cnaes_secundarios": cnaes_secundarios,
                    "cep": cep,
                    "logradouro": logradouro,
                    "numero": numero,
                    "complemento": complemento,
                    "bairro": bairro,
                    "municipio": municipio,
                    "uf": uf,
                    "qsa": qsa,
                }

                ok, msg, empresa_id = criar_empresa(nome_oficial, cnpj_oficial, email, telefone, senha, dados_cadastrais)

                if ok:
                    st.session_state["logado"] = True
                    st.session_state["empresa_id"] = empresa_id
                    st.session_state["empresa_nome"] = nome_oficial
                    st.success(msg)
                    st.rerun()
                else:
                    st.warning(msg)

    st.stop()

preparar_banco()
inicializar_schema_goia()
suspender_testes_expirados()
garantir_enriquecimento_cadastral()
garantir_motor_encerramento()
garantir_schema_documental()
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
    except:
        receber = pd.DataFrame(columns=["data", "tipo", "descricao", "categoria", "valor", "status"])

    try:
        pagar = pd.read_sql_query("""
            SELECT data_vencimento AS data, 'Pagar' AS tipo, descricao, categoria, -valor AS valor, status
            FROM contas_pagar
            WHERE empresa_id = ?
        """, conn, params=(EMPRESA_ID,))
    except:
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