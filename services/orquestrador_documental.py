from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from utils.db import conectar_banco
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any


@dataclass
class ResultadoProcessamento:
    sucesso: bool
    tipo_documento: str
    documento_id: int | None = None
    processo_id: int | None = None
    cliente_id: int | None = None
    fornecedor_id: int | None = None
    conta_receber_id: int | None = None
    conta_pagar_id: int | None = None
    mensagem: str = ""
    diagnostico: str = ""


def conectar() -> sqlite3.Connection:
    conn = conectar_banco()
    conn.row_factory = sqlite3.Row
    return conn


def agora_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def calcular_hash(conteudo: bytes) -> str:
    return hashlib.sha256(conteudo).hexdigest()


def somente_digitos(valor: str | None) -> str:
    if not valor:
        return ""
    return "".join(ch for ch in str(valor) if ch.isdigit())


def detectar_tipo_documento(nome_arquivo: str, conteudo: bytes) -> str:
    nome = nome_arquivo.lower()
    texto_inicio = conteudo[:5000].decode("utf-8", errors="ignore").lower()

    if nome.endswith(".ofx") or "<ofx" in texto_inicio:
        return "OFX"

    if nome.endswith(".xml") and ("<nfeproc" in texto_inicio or "<nfe" in texto_inicio):
        return "NF-e"

    if nome.endswith(".xml"):
        return "XML"

    if nome.endswith(".pdf"):
        return "PDF"

    if nome.endswith(".csv"):
        return "CSV"

    if nome.endswith(".txt"):
        return "TXT"

    return "DESCONHECIDO"


def registrar_documento_bruto(
    *,
    empresa_id: int,
    nome_arquivo: str,
    conteudo: bytes,
    tipo_documento: str,
    dados_extraidos: dict[str, Any] | None = None,
    diagnostico: str | None = None,
) -> int:
    hash_arquivo = calcular_hash(conteudo)
    extensao = Path(nome_arquivo).suffix.lower().replace(".", "")
    texto_extraido = conteudo.decode("utf-8", errors="ignore")

    with conectar() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO documentos (
                empresa_id,
                nome_arquivo,
                tipo_documento,
                origem,
                status,
                status_processamento,
                texto_extraido,
                conteudo_texto,
                hash_arquivo,
                extensao,
                tamanho_bytes,
                diagnostico_tecnico,
                dados_extraidos_json,
                criado_em,
                processado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                empresa_id,
                nome_arquivo,
                tipo_documento,
                "Upload",
                "Importado",
                "Registrado",
                texto_extraido,
                texto_extraido,
                hash_arquivo,
                extensao,
                len(conteudo),
                diagnostico or "",
                json.dumps(dados_extraidos or {}, ensure_ascii=False),
                agora_iso(),
                agora_iso(),
            ),
        )

        return int(cur.lastrowid)


def processar_documento_upload(
    *,
    empresa_id: int,
    nome_arquivo: str,
    conteudo: bytes,
) -> ResultadoProcessamento:
    try:
        tipo = detectar_tipo_documento(nome_arquivo, conteudo)

        documento_id = registrar_documento_bruto(
            empresa_id=empresa_id,
            nome_arquivo=nome_arquivo,
            conteudo=conteudo,
            tipo_documento=tipo,
            dados_extraidos={"tipo_detectado": tipo},
            diagnostico="Documento registrado pela camada inicial de orquestração.",
        )

        return ResultadoProcessamento(
            sucesso=True,
            tipo_documento=tipo,
            documento_id=documento_id,
            mensagem="Documento registrado com sucesso pela orquestração inicial.",
            diagnostico="Primeira etapa concluída: detecção de tipo e registro bruto.",
        )

    except Exception as e:
        return ResultadoProcessamento(
            sucesso=False,
            tipo_documento="ERRO",
            mensagem="Falha ao processar documento.",
            diagnostico=str(e),
        )


def resultado_para_dict(resultado: ResultadoProcessamento) -> dict[str, Any]:
    return asdict(resultado)
