from pathlib import Path

p = Path("pages/1_Importar_Documento.py")
txt = p.read_text(encoding="utf-8")

txt = txt.replace("descricao = extrair_tag_ofx(bloco, \"MEMO\") or extrair_tag_ofx(bloco, \"NAME\") or \"Movimento OFX\"", "historico = extrair_tag_ofx(bloco, \"MEMO\") or extrair_tag_ofx(bloco, \"NAME\") or \"Movimento OFX\"")
txt = txt.replace("documento = extrair_tag_ofx(bloco, \"FITID\")\n        tipo =", "fitid = extrair_tag_ofx(bloco, \"FITID\")\n        tipo =")

txt = txt.replace("""
            WHERE empresa_id = ?
              AND IFNULL(documento, '') = IFNULL(?, '')
              AND IFNULL(data_movimento, '') = IFNULL(?, '')
              AND IFNULL(valor, 0) = IFNULL(?, 0)
              AND IFNULL(origem, '') = IFNULL(?, '')
        """, (EMPRESA_ID_ATIVA, documento, data_movimento, valor, nome_arquivo))
""", """
            WHERE empresa_id = ?
              AND IFNULL(data_movimento, '') = IFNULL(?, '')
              AND IFNULL(valor, 0) = IFNULL(?, 0)
              AND IFNULL(historico, '') = IFNULL(?, '')
        """, (EMPRESA_ID_ATIVA, data_movimento, valor, historico))
""")

txt = txt.replace("""
            INSERT INTO movimentos_bancarios (
                empresa_id,
                data_movimento,
                descricao,
                documento,
                valor,
                tipo,
                conciliado,
                origem
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            EMPRESA_ID_ATIVA,
            data_movimento,
            descricao[:250],
            documento,
            valor,
            tipo,
            0,
            nome_arquivo
        ))
""", """
            INSERT INTO movimentos_bancarios (
                empresa_id,
                data_movimento,
                historico,
                valor,
                tipo,
                conciliado,
                cnpj_origem,
                nome_origem
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            EMPRESA_ID_ATIVA,
            data_movimento,
            historico[:250],
            valor,
            tipo,
            0,
            "",
            nome_arquivo
        ))
""")

p.write_text(txt, encoding="utf-8")
print("OFX alinhado ao schema real de movimentos_bancarios.")
