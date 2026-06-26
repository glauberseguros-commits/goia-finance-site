from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from controllers.documento_nfe_controller import DocumentoNFeController
from schemas.documento_fiscal_schema import DocumentoFiscalDTO


XML_NFE = b"""<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
  <NFe>
    <infNFe Id="NFe00000000000000000000000000000000000000000000">
      <ide>
        <serie>1</serie>
        <nNF>12345</nNF>
        <dhEmi>2026-06-26T10:45:00-03:00</dhEmi>
      </ide>
      <emit>
        <CNPJ>28860122000177</CNPJ>
        <xNome>GODS PRODUTOS SERVICOS E EVENTOS LTDA</xNome>
      </emit>
      <dest>
        <CNPJ>11222333000181</CNPJ>
        <xNome>CLIENTE TESTE LTDA</xNome>
      </dest>
      <det nItem="1">
        <prod>
          <cProd>001</cProd>
          <xProd>Produto Teste</xProd>
          <NCM>84713012</NCM>
          <CFOP>5102</CFOP>
          <qCom>2.0000</qCom>
          <vUnCom>100.00</vUnCom>
          <vProd>200.00</vProd>
        </prod>
      </det>
      <total>
        <ICMSTot>
          <vNF>200.00</vNF>
        </ICMSTot>
      </total>
    </infNFe>
  </NFe>
</nfeProc>
"""


def test_parser_nfe_xml_dto():
    doc = DocumentoNFeController.ler_dto(XML_NFE)

    assert isinstance(doc, DocumentoFiscalDTO)
    assert doc.numero == "12345"
    assert doc.serie == "1"
    assert doc.emitente.cnpj == "28860122000177"
    assert doc.destinatario.cnpj == "11222333000181"
    assert doc.valor_total == 200.0
    assert len(doc.itens) == 1
    assert doc.itens[0].descricao == "Produto Teste"

    print("OK - Parser NF-e DTO válido.")


if __name__ == "__main__":
    test_parser_nfe_xml_dto()
