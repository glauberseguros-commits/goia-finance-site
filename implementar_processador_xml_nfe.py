from pathlib import Path

p = Path("pages/1_Importar_Documento.py")
txt = p.read_text(encoding="utf-8")

if "import xml.etree.ElementTree as ET" not in txt:
    txt = txt.replace("import re", "import re\nimport xml.etree.ElementTree as ET")

marcador = "\ndef analisar_documento(texto):"

func = r'''

def tag_texto_xml(root, nome_tag):
    for elem in root.iter():
        if elem.tag.endswith(nome_tag):
            return (elem.text or "").strip()
    return ""


def normalizar_xml_valor(valor):
    try:
        return float(str(valor or "0").replace(",", "."))
    except Exception:
        return 0.0


def analisar_xml_nfe(conteudo_xml):
    texto_xml = conteudo_xml or ""

    try:
        root = ET.fromstring(texto_xml)
    except Exception:
        return {
            "tipo_detectado": "XML",
            "direcao_sugerida": "XML - Conferência necessária",
            "documentos_encontrados": encontrar_documentos(texto_xml),
            "entidades_extraidas": extrair_entidades_documento(texto_xml),
            "parte_cnpj": "",
            "parte_nome": "",
            "valor": maior_valor(texto_xml),
            "data_emissao": None,
            "data_vencimento": None,
            "chave_acesso_nfe": "",
            "numero_nfe": "",
            "serie_nfe": "",
            "emitente_cnpj": "",
            "emitente_nome": "",
            "destinatario_cnpj": "",
            "destinatario_nome": "",
        }

    chave = ""
    inf_nfe = None

    for elem in root.iter():
        if elem.tag.endswith("infNFe"):
            inf_nfe = elem
            chave = elem.attrib.get("Id", "").replace("NFe", "").strip()
            break

    emitente_cnpj = ""
    emitente_nome = ""
    destinatario_cnpj = ""
    destinatario_nome = ""

    if inf_nfe is not None:
        for elem in inf_nfe.iter():
            if elem.tag.endswith("emit"):
                emitente_cnpj = tag_texto_xml(elem, "CNPJ") or tag_texto_xml(elem, "CPF")
                emitente_nome = tag_texto_xml(elem, "xNome")
                break

        for elem in inf_nfe.iter():
            if elem.tag.endswith("dest"):
                destinatario_cnpj = tag_texto_xml(elem, "CNPJ") or tag_texto_xml(elem, "CPF")
                destinatario_nome = tag_texto_xml(elem, "xNome")
                break

    numero = tag_texto_xml(root, "nNF")
    serie = tag_texto_xml(root, "serie")
    data_emissao_raw = tag_texto_xml(root, "dhEmi") or tag_texto_xml(root, "dEmi")
    data_emissao = data_emissao_raw[:10] if data_emissao_raw else None
    valor = normalizar_xml_valor(tag_texto_xml(root, "vNF"))

    doc_empresa = somente_numeros(DOC_EMPRESA_LOGADA)
    emitente_num = somente_numeros(emitente_cnpj)
    destinatario_num = somente_numeros(destinatario_cnpj)

    if emitente_num == doc_empresa:
        direcao = "Nota Fiscal de Venda"
        parte_cnpj = normalizar_documento(destinatario_cnpj)
        parte_nome = destinatario_nome
    elif destinatario_num == doc_empresa:
        direcao = "Nota Fiscal de Compra"
        parte_cnpj = normalizar_documento(emitente_cnpj)
        parte_nome = emitente_nome
    else:
        direcao = "Nota Fiscal - Conferência necessária"
        parte_cnpj = normalizar_documento(destinatario_cnpj or emitente_cnpj)
        parte_nome = destinatario_nome or emitente_nome

    return {
        "tipo_detectado": "Nota Fiscal",
        "direcao_sugerida": direcao,
        "documentos_encontrados": encontrar_documentos(texto_xml),
        "entidades_extraidas": extrair_entidades_documento(texto_xml),
        "parte_cnpj": parte_cnpj,
        "parte_nome": parte_nome,
        "valor": valor,
        "data_emissao": data_emissao,
        "data_vencimento": data_emissao,
        "chave_acesso_nfe": chave,
        "numero_nfe": numero,
        "serie_nfe": serie,
        "emitente_cnpj": normalizar_documento(emitente_cnpj),
        "emitente_nome": emitente_nome,
        "destinatario_cnpj": normalizar_documento(destinatario_cnpj),
        "destinatario_nome": destinatario_nome,
    }
'''

if "def analisar_xml_nfe(" not in txt:
    txt = txt.replace(marcador, func + marcador)

txt = txt.replace(
'''                elif extensao in ["ofx", "csv", "txt", "xml"]:
                    conteudo = arquivo.getvalue()
                    try:
                        texto = conteudo.decode("utf-8")
                    except Exception:
                        try:
                            texto = conteudo.decode("latin-1")
                        except Exception:
                            texto = ""

                    analise = {
                        "tipo_detectado": "Arquivo estruturado",
                        "direcao_sugerida": f"{extensao.upper()} - Processador pendente",
                        "documentos_encontrados": encontrar_documentos(texto),
                        "parte_cnpj": "",
                        "parte_nome": "",
                        "valor": maior_valor(texto),
                        "data_emissao": None,
                        "data_vencimento": None,
                        "chave_acesso_nfe": "",
                        "numero_nfe": "",
                        "serie_nfe": "",
                    }

                    st.warning(f"Arquivo {extensao.upper()} aceito. Processador específico ainda será implementado.")
                    continue''',
'''                elif extensao == "xml":
                    conteudo = arquivo.getvalue()
                    try:
                        texto = conteudo.decode("utf-8")
                    except Exception:
                        try:
                            texto = conteudo.decode("latin-1")
                        except Exception:
                            texto = ""

                    analise = analisar_xml_nfe(texto)

                elif extensao in ["ofx", "csv", "txt"]:
                    conteudo = arquivo.getvalue()
                    try:
                        texto = conteudo.decode("utf-8")
                    except Exception:
                        try:
                            texto = conteudo.decode("latin-1")
                        except Exception:
                            texto = ""

                    analise = {
                        "tipo_detectado": "Arquivo estruturado",
                        "direcao_sugerida": f"{extensao.upper()} - Processador pendente",
                        "documentos_encontrados": encontrar_documentos(texto),
                        "parte_cnpj": "",
                        "parte_nome": "",
                        "valor": maior_valor(texto),
                        "data_emissao": None,
                        "data_vencimento": None,
                        "chave_acesso_nfe": "",
                        "numero_nfe": "",
                        "serie_nfe": "",
                    }

                    st.warning(f"Arquivo {extensao.upper()} aceito. Processador específico ainda será implementado.")
                    continue'''
)

p.write_text(txt, encoding="utf-8")

print("Processador XML NF-e implementado.")
