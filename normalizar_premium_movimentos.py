from pathlib import Path
import re

p = Path("pages/8_Movimentos_Bancarios.py")
txt = p.read_text(encoding="utf-8")

txt = re.sub(
    r'st\.set_page_config\(\s*page_title="Movimentos Bancários",\s*page_icon=".*?",\s*layout="wide"\s*\)',
    'st.set_page_config(\n    page_title="Movimentos Bancarios",\n    page_icon="GOIA",\n    layout="wide"\n)',
    txt,
    count=1,
    flags=re.S
)

txt = re.sub(
    r'hero\(\s*"Movimentos Bancarios",\s*".*?",\s*icone=".*?"\s*\)',
    '''hero(
    "Movimentos Bancarios",
    "Central de auditoria financeira para extratos OFX, conciliacao bancaria e rastreabilidade de movimentacoes.",
    icone="GOIA"
)''',
    txt,
    count=1,
    flags=re.S
)

p.write_text(txt, encoding="utf-8")
print("Movimentos Bancarios normalizado.")
