from pathlib import Path

p = Path("pages/1_Importar_Documento.py")
txt = p.read_text(encoding="utf-8")

txt = txt.replace(
'''                texto = extrair_texto_pdf(arquivo)
                analise = analisar_documento(texto)

                c1, c2, c3 = st.columns(3)
                c1.metric("Tipo", analise["tipo_detectado"])
                c2.metric("Classificação", analise["direcao_sugerida"])
                c3.metric("Valor", moeda(analise["valor"]))''',
'''                extensao = arquivo.name.lower().split(".")[-1]

                if extensao == "pdf":
                    texto = extrair_texto_pdf(arquivo)
                    analise = analisar_documento(texto)

                elif extensao in ["ofx", "csv", "txt", "xml"]:
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
                    st.stop()

                else:
                    st.error(f"Formato não suportado: {extensao}")
                    st.stop()

                c1, c2, c3 = st.columns(3)
                c1.metric("Tipo", analise["tipo_detectado"])
                c2.metric("Classificação", analise["direcao_sugerida"])
                c3.metric("Valor", moeda(analise["valor"]))'''
)

p.write_text(txt, encoding="utf-8")

print("Desvio por extensão implementado.")
