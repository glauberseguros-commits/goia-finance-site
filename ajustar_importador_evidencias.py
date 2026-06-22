from pathlib import Path

p = Path("pages/1_Importar_Documento.py")
txt = p.read_text(encoding="utf-8")

if "def criar_evidencia_documental(" not in txt:
    marcador = "\ndef criar_processo_documental(cursor, documento_id, analise):"

    func = r'''

def criar_evidencia_documental(cursor, processo_id, documento_id, analise, conta_receber_id=None, conta_pagar_id=None):
    tipo = analise.get("tipo_detectado") or "Documento"
    numero = analise.get("numero_nfe") or ""
    serie = analise.get("serie_nfe") or ""
    valor = float(analise.get("valor") or 0)
    data_ref = analise.get("data_emissao") or analise.get("data_vencimento")
    origem = "Importação documental"

    descricao = tipo

    if numero:
        descricao = f"{tipo} {numero}"
        if serie:
            descricao += f" Série {serie}"

    cursor.execute("""
        INSERT INTO evidencias (
            empresa_id,
            processo_id,
            documento_id,
            conta_receber_id,
            conta_pagar_id,
            tipo_evidencia,
            descricao,
            origem,
            valor,
            data_referencia,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        EMPRESA_ID_ATIVA,
        processo_id,
        documento_id,
        conta_receber_id,
        conta_pagar_id,
        tipo,
        descricao,
        origem,
        valor,
        data_ref,
        "Ativa"
    ))

    evidencia_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO processo_evidencias (
            empresa_id,
            processo_id,
            documento_id,
            tipo_evidencia,
            descricao,
            valor,
            data_evidencia,
            origem,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        EMPRESA_ID_ATIVA,
        processo_id,
        documento_id,
        tipo,
        descricao,
        valor,
        data_ref,
        origem,
        "Validada"
    ))

    return evidencia_id
'''

    txt = txt.replace(marcador, func + marcador)

# Ajusta criação de conta a receber para capturar o ID
txt = txt.replace(
'''            cur.execute("""
                INSERT INTO contas_receber (
                    cliente_id, documento_id, descricao, categoria, valor,
                    data_emissao, data_vencimento, status, empresa_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cliente_id, documento_id, descricao, "Vendas", valor,
                analise.get("data_emissao"), analise.get("data_vencimento"), "Pendente", EMPRESA_ID_ATIVA
            ))

            acoes.append("Venda e conta a receber criadas.")''',
'''            cur.execute("""
                INSERT INTO contas_receber (
                    cliente_id, documento_id, descricao, categoria, valor,
                    data_emissao, data_vencimento, status, empresa_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cliente_id, documento_id, descricao, "Vendas", valor,
                analise.get("data_emissao"), analise.get("data_vencimento"), "Pendente", EMPRESA_ID_ATIVA
            ))

            conta_receber_id = cur.lastrowid

            acoes.append("Venda e conta a receber criadas.")'''
)

# Ajusta criação de conta a pagar para capturar o ID
txt = txt.replace(
'''            cur.execute("""
                INSERT INTO contas_pagar (
                    fornecedor_id, documento_id, descricao, categoria, valor,
                    data_emissao, data_vencimento, status, empresa_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fornecedor_id, documento_id, descricao, "Compras", valor,
                analise.get("data_emissao"), analise.get("data_vencimento"), "Pendente", EMPRESA_ID_ATIVA
            ))

            acoes.append("Compra e conta a pagar criadas.")''',
'''            cur.execute("""
                INSERT INTO contas_pagar (
                    fornecedor_id, documento_id, descricao, categoria, valor,
                    data_emissao, data_vencimento, status, empresa_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fornecedor_id, documento_id, descricao, "Compras", valor,
                analise.get("data_emissao"), analise.get("data_vencimento"), "Pendente", EMPRESA_ID_ATIVA
            ))

            conta_pagar_id = cur.lastrowid

            acoes.append("Compra e conta a pagar criadas.")'''
)

# Inicializa variáveis de vínculo no início do salvamento
txt = txt.replace(
'''    documento_id = cur.lastrowid
    acoes = ["Documento salvo."]''',
'''    documento_id = cur.lastrowid
    conta_receber_id = None
    conta_pagar_id = None
    acoes = ["Documento salvo."]'''
)

# Cria evidência logo após criar processo documental
txt = txt.replace(
'''    processo_id = criar_processo_documental(cur, documento_id, analise)
    acoes.append("Processo documental e pendências criados.")''',
'''    processo_id = criar_processo_documental(cur, documento_id, analise)

    criar_evidencia_documental(
        cur,
        processo_id,
        documento_id,
        analise,
        conta_receber_id=conta_receber_id,
        conta_pagar_id=conta_pagar_id
    )

    acoes.append("Processo documental, evidência e pendências criados.")'''
)

p.write_text(txt, encoding="utf-8")

print("Importador ajustado para criar evidência documental automaticamente.")
