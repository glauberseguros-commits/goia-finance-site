"""
Serviço operacional do Admin GOIA.

Centraliza métricas, listagens e ações administrativas para o Control Center.
"""

import pandas as pd

from utils.db import conectar_banco
from formatters.telefone_formatter import formatar_telefone


def _df(query, params=()):
    conn = conectar_banco()
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def obter_metricas_admin():
    conn = conectar_banco()
    cur = conn.cursor()

    def count(query, params=()):
        try:
            return cur.execute(query, params).fetchone()[0] or 0
        except Exception:
            return 0

    metricas = {
        "assinantes": count("SELECT COUNT(*) FROM empresas"),
        "ativos": count("SELECT COUNT(*) FROM empresas WHERE COALESCE(status_assinatura,'Ativa') = 'Ativa'"),
        "em_teste": count("SELECT COUNT(*) FROM empresas WHERE COALESCE(plano,'') = 'Teste'"),
        "suspensos": count("SELECT COUNT(*) FROM empresas WHERE COALESCE(status_assinatura,'') = 'Suspensa'"),
        "bloqueados": count("SELECT COUNT(*) FROM empresas WHERE COALESCE(status_assinatura,'') = 'Bloqueada'"),
        "documentos": count("SELECT COUNT(*) FROM documentos"),
        "clientes": count("SELECT COUNT(*) FROM clientes"),
        "fornecedores": count("SELECT COUNT(*) FROM fornecedores"),
        "processos": count("SELECT COUNT(*) FROM processos_documentais"),
    }

    conn.close()
    return metricas


def listar_assinantes_admin():
    df = _df("""
        SELECT
            id,
            nome,
            nome_fantasia,
            cnpj_cpf,
            email,
            telefone,
            plano,
            status_assinatura,
            data_inicio_assinatura,
            data_fim_assinatura,
            criado_em,
            atualizado_em
        FROM empresas
        ORDER BY id DESC
    """)

    if not df.empty and "telefone" in df.columns:
        df["telefone"] = df["telefone"].apply(formatar_telefone)

    return df


def buscar_assinante_admin(empresa_id):
    df = _df("""
        SELECT *
        FROM empresas
        WHERE id = ?
        LIMIT 1
    """, (empresa_id,))

    if df.empty:
        return None

    return df.iloc[0].to_dict()


def alterar_status_assinante(empresa_id, status, motivo=""):
    conn = conectar_banco()
    cur = conn.cursor()

    cur.execute("""
        UPDATE empresas
        SET status_assinatura = ?,
            motivo_bloqueio = ?,
            atualizado_em = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (status, motivo, empresa_id))

    conn.commit()
    conn.close()


def alterar_plano_assinante(empresa_id, plano, data_inicio=None, data_fim=None):
    conn = conectar_banco()
    cur = conn.cursor()

    cur.execute("""
        UPDATE empresas
        SET plano = ?,
            data_inicio_assinatura = COALESCE(?, data_inicio_assinatura),
            data_fim_assinatura = COALESCE(?, data_fim_assinatura),
            atualizado_em = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (plano, data_inicio, data_fim, empresa_id))

    conn.commit()
    conn.close()


def excluir_assinante_admin(empresa_id):
    conn = conectar_banco()
    cur = conn.cursor()

    cur.execute("DELETE FROM empresas WHERE id = ?", (empresa_id,))

    conn.commit()
    conn.close()

def pesquisar_assinantes(df, texto):

    if df.empty:
        return df

    texto = str(texto or "").strip().lower()

    if not texto:
        return df

    campos = [
        "nome",
        "nome_fantasia",
        "cnpj_cpf",
        "email",
        "telefone",
        "status_assinatura",
        "plano",
    ]

    mascara = False

    for campo in campos:
        if campo in df.columns:
            serie = df[campo].fillna("").astype(str).str.lower()
            mascara = mascara | serie.str.contains(texto, regex=False)

    return df[mascara].copy()


def ordenar_assinantes(df):

    if df.empty:
        return df

    if "nome" in df.columns:
        return df.sort_values("nome")

    return df


def resumo_assinante(empresa):

    if not empresa:
        return {}

    return {
        "id": empresa.get("id"),
        "empresa": empresa.get("nome"),
        "fantasia": empresa.get("nome_fantasia"),
        "cnpj": empresa.get("cnpj_cpf"),
        "plano": empresa.get("plano"),
        "status": empresa.get("status_assinatura"),
        "email": empresa.get("email"),
        "telefone": empresa.get("telefone"),
    }

