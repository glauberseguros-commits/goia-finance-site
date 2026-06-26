from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.documento_service import inserir_documento_com_cursor
from services.cliente_service import obter_ou_criar_cliente_com_cursor
from services.fornecedor_service import obter_ou_criar_fornecedor_com_cursor


@dataclass
class ResultadoImportacao:
    documento_id: int | None = None
    processo_id: int | None = None
    conta_receber_id: int | None = None
    conta_pagar_id: int | None = None
    cliente_id: int | None = None
    fornecedor_id: int | None = None
    acoes: list[str] | None = None


class ImportacaoDocumentalService:

    def __init__(
        self,
        cursor,
        empresa_id: int,
    ):
        self.cursor = cursor
        self.empresa_id = empresa_id

    def registrar_documento(self, **dados):
        return inserir_documento_com_cursor(
            self.cursor,
            **dados,
        )

    def obter_ou_criar_cliente(self, **kwargs):
        return obter_ou_criar_cliente_com_cursor(
            cursor=self.cursor,
            empresa_id=self.empresa_id,
            **kwargs,
        )

    def obter_ou_criar_fornecedor(self, **kwargs):
        return obter_ou_criar_fornecedor_com_cursor(
            cursor=self.cursor,
            empresa_id=self.empresa_id,
            **kwargs,
        )

    def processar(
        self,
        nome_arquivo: str,
        texto: str,
        analise: dict[str, Any],
    ) -> ResultadoImportacao:
        """
        Camada de aplicação.

        Nesta primeira etapa ela funciona como ponto único
        para receber toda a lógica de importação.

        Os próximos commits irão mover gradualmente a lógica
        atualmente existente em salvar_documento_erp()
        para dentro desta classe.
        """

        return ResultadoImportacao(
            acoes=[
                "Estrutura da camada de aplicação criada."
            ]
        )
