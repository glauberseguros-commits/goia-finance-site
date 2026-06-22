from pathlib import Path

p = Path("pages/1_Importar_Documento.py")
txt = p.read_text(encoding="utf-8")

antigo = '''        if "ADMINISTRAÇÃO REGIONAL DE SOBRADINHO" in t or "ADMINISTRACAO REGIONAL DE SOBRADINHO" in t:
            parte_nome = "ADMINISTRAÇÃO REGIONAL DE SOBRADINHO"
        elif "COMANDO DA MARINHA" in t:
            parte_nome = "COMANDO DA MARINHA"
        elif "ESTADO-MAIOR DA ARMADA" in t:
            parte_nome = "ESTADO-MAIOR DA ARMADA"
        else:
            parte_nome = "Órgão Público"
'''

novo = '''        parte_nome = "Órgão Público"
'''

txt = txt.replace(antigo, novo)

p.write_text(txt, encoding="utf-8")

print("Regras fixas restantes removidas da Nota de Empenho.")
