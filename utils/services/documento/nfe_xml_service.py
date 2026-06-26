"""
Parser estrutural de NF-e XML.

Responsável por transformar um XML da NF-e
em um dicionário padronizado da GOIA.
"""

from xml.etree import ElementTree as ET

from schemas.documento_fiscal_schema import DocumentoFiscalDTO, PessoaFiscalDTO, ItemFiscalDTO


NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}


def _texto(node, path):
    item = node.find(path, NS)
    return item.text.strip() if item is not None and item.text else ""


def ler_nfe_xml(xml_bytes):

    root = ET.fromstring(xml_bytes)

    inf = root.find(".//nfe:infNFe", NS)

    emit = inf.find("nfe:emit", NS)
    dest = inf.find("nfe:dest", NS)
    ide = inf.find("nfe:ide", NS)
    total = inf.find("nfe:total/nfe:ICMSTot", NS)

    dados = {

        "numero": _texto(ide, "nfe:nNF"),
        "serie": _texto(ide, "nfe:serie"),
        "data_emissao": _texto(ide, "nfe:dhEmi"),

        "emitente": {
            "cnpj": _texto(emit, "nfe:CNPJ"),
            "nome": _texto(emit, "nfe:xNome"),
        },

        "destinatario": {
            "cnpj": _texto(dest, "nfe:CNPJ"),
            "cpf": _texto(dest, "nfe:CPF"),
            "nome": _texto(dest, "nfe:xNome"),
        },

        "valor_total": float(_texto(total, "nfe:vNF") or 0),

        "itens": []
    }

    for det in inf.findall("nfe:det", NS):

        prod = det.find("nfe:prod", NS)

        dados["itens"].append({

            "codigo": _texto(prod, "nfe:cProd"),
            "descricao": _texto(prod, "nfe:xProd"),
            "ncm": _texto(prod, "nfe:NCM"),
            "cfop": _texto(prod, "nfe:CFOP"),
            "quantidade": float(_texto(prod, "nfe:qCom") or 0),
            "valor_unitario": float(_texto(prod, "nfe:vUnCom") or 0),
            "valor_total": float(_texto(prod, "nfe:vProd") or 0),

        })

    return dados



def ler_nfe_xml_dto(xml_bytes):
    dados = ler_nfe_xml(xml_bytes)

    doc = DocumentoFiscalDTO(
        numero=dados.get("numero", ""),
        serie=dados.get("serie", ""),
        data_emissao=dados.get("data_emissao", ""),
        emitente=PessoaFiscalDTO(
            cnpj=dados.get("emitente", {}).get("cnpj", ""),
            nome=dados.get("emitente", {}).get("nome", ""),
        ),
        destinatario=PessoaFiscalDTO(
            cnpj=dados.get("destinatario", {}).get("cnpj", ""),
            cpf=dados.get("destinatario", {}).get("cpf", ""),
            nome=dados.get("destinatario", {}).get("nome", ""),
        ),
        valor_total=dados.get("valor_total", 0.0),
    )

    for item in dados.get("itens", []):
        doc.itens.append(ItemFiscalDTO(
            codigo=item.get("codigo", ""),
            descricao=item.get("descricao", ""),
            ncm=item.get("ncm", ""),
            cfop=item.get("cfop", ""),
            quantidade=item.get("quantidade", 0.0),
            valor_unitario=item.get("valor_unitario", 0.0),
            valor_total=item.get("valor_total", 0.0),
        ))

    return doc
