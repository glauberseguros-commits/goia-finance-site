from pathlib import Path
import re

txt = Path("pages/1_Importar_Documento.py").read_text(
    encoding="utf-8"
)

funcoes = [
    "encontrar_documentos",
    "identificar_nome_por_documento",
    "extrair_partes_nfe",
    "analisar_documento",
    "salvar_documento_erp"
]

for nome in funcoes:
    print("\n" + "=" * 80)
    print(nome)
    print("=" * 80)

    m = re.search(
        rf"def {nome}\(.*?(?=\ndef |\Z)",
        txt,
        flags=re.S
    )

    if m:
        print(m.group(0))
    else:
        print("FUNÇÃO NÃO ENCONTRADA")
