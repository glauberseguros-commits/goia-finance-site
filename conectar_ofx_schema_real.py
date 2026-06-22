from pathlib import Path
import re

p = Path("pages/1_Importar_Documento.py")
txt = p.read_text(encoding="utf-8")

nova_funcao = r'''
def extrair_tag_ofx(bloco, tag):
    m = re.search(rf"<{tag}>(.*?)(?:\n|<)", bloco or "", flags=re.I | re.S)
    return m.group(1).strip() if m else ""


def converter_data_ofx(valor):
    nums = somente_numeros(valor)
    if len(nums) >= 8:
        return f"{nums[:4]}-{nums[4:6]}-{nums[6:8]}"
    return None


def converter_valor_ofx(valor):
    try:
        return float(str(valor or "0").replace(",", ".").strip())
    except Exception:
        return 0.0


def processar_ofx_bancario(nome_arquivo, texto):
    garantir_estrutura_movimentos_bancarios()

    blocos = re.findall(
        r"<STMTTRN>(.*?)(?=<STMTTRN>|</BANKTRANLIST>|</OFX>)",
        texto or "",
        flags=re.I | re.S
    )

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO extratos_bancarios (
            nome_arquivo,
            empresa_id
        )
        VALUES (?, ?)
    """, (
        nome_arquivo,
        EMPRESA_ID_ATIVA
    ))

    extrato_id = cur.lastrowid

    inseridos = 0
    ignorados = 0

    for bloco in blocos:
        data_movimento = converter_data_ofx(extrair_tag_ofx(bloco, "DTPOSTED"))
        valor = converter_valor_ofx(extrair_tag_ofx(bloco, "TRNAMT"))
        historico = (
            extrair_tag_ofx(bloco, "MEMO")
            or extrair_tag_ofx(bloco, "NAME")
            or "Movimento OFX"
        )
        tipo = "Credito" if valor > 0 else "Debito"

        cur.execute("""
            SELECT id
            FROM movimentos_bancarios
            WHERE empresa_id = ?
              AND IFNULL(data_movimento, '') = IFNULL(?, '')
              AND IFNULL(valor, 0) = IFNULL(?, 0)
              AND IFNULL(historico, '') = IFNULL(?, '')
        """, (
            EMPRESA_ID_ATIVA,
            data_movimento,
            valor,
            historico
        ))

        if cur.fetchone():
            ignorados += 1
            continue

        cur.execute("""
            INSERT INTO movimentos_bancarios (
                extrato_id,
                empresa_id,
                data_movimento,
                historico,
                valor,
                tipo,
                conciliado,
                nome_origem
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            extrato_id,
            EMPRESA_ID_ATIVA,
            data_movimento,
            historico[:250],
            valor,
            tipo,
            0,
            nome_arquivo
        ))

        inseridos += 1

    conn.commit()
    conn.close()

    return {
        "tipo_detectado": "Extrato Bancário",
        "direcao_sugerida": "OFX - Movimentos bancários importados",
        "total_movimentos": len(blocos),
        "movimentos_inseridos": inseridos,
        "movimentos_ignorados": ignorados,
        "extrato_id": extrato_id,
    }


'''

padrao = r'def extrair_tag_ofx\(bloco, tag\):.*?(?=st\.title\("📄 Importar Documento Financeiro"\))'

txt2, n = re.subn(padrao, nova_funcao, txt, count=1, flags=re.S)

if n != 1:
    raise SystemExit(f"Bloco OFX não substituído. Substituições: {n}")

p.write_text(txt2, encoding="utf-8")
print("Importador OFX conectado ao schema real.")
