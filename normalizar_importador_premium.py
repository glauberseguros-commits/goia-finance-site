from pathlib import Path
import re

p = Path("pages/1_Importar_Documento.py")
txt = p.read_text(encoding="utf-8")

txt = re.sub(
    r'st\.set_page_config\(page_title="Importar Documento", page_icon=".*?", layout="wide"\)',
    'st.set_page_config(page_title="Importar Documento", page_icon="GOIA", layout="wide")',
    txt,
    count=1
)

txt = re.sub(
    r'hero\(\s*"Central de Documentos",\s*".*?",\s*icone=".*?"\s*\)',
    '''hero(
    "Central de Documentos",
    "Envie NF-e, OFX, boletos, comprovantes, notas de empenho e documentos cadastrais. A GOIA identifica entidades, cria evidencias, pendencias e movimentacoes financeiras automaticamente.",
    icone="GOIA"
)''',
    txt,
    count=1,
    flags=re.S
)

p.write_text(txt, encoding="utf-8")
print("Importador premium normalizado sem caracteres especiais.")
