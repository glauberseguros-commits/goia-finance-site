from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from schemas.documento_fiscal_schema import (
    DocumentoFiscalDTO,
    PessoaFiscalDTO,
    ItemFiscalDTO,
)


def test_documento_fiscal_schema():

    doc = DocumentoFiscalDTO()

    assert isinstance(doc.emitente, PessoaFiscalDTO)
    assert isinstance(doc.destinatario, PessoaFiscalDTO)

    doc.itens.append(ItemFiscalDTO())

    assert len(doc.itens) == 1

    print("OK - DocumentoFiscalDTO válido.")


if __name__ == "__main__":
    test_documento_fiscal_schema()
