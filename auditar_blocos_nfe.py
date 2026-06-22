from pathlib import Path
import re

txt = Path("pages/1_Importar_Documento.py").read_text(
    encoding="utf-8"
)

for nome in [
    "extrair_texto_pdf",
    "extrair_partes_nfe",
    "analisar_documento"
]:
    print()
    print("=" * 100)
    print(nome)
    print("=" * 100)

    m = re.search(
        rf"def {nome}\(.*?(?=\ndef |\Z)",
        txt,
        flags=re.S
    )

    if m:
        print(m.group(0))
    else:
        print("FUNÇÃO NÃO ENCONTRADA")
