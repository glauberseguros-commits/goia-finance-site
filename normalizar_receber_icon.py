from pathlib import Path
import re

p = Path("pages/2_Contas_a_Receber.py")
txt = p.read_text(encoding="utf-8")

txt = re.sub(
    r'page_icon=".*?"',
    'page_icon="GOIA"',
    txt,
    count=1
)

p.write_text(txt, encoding="utf-8")
print("Icone normalizado em Contas a Receber.")
