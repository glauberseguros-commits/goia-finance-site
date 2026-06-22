from pathlib import Path

p = Path("pages/3_Contas_a_Pagar.py")
txt = p.read_text(encoding="utf-8")

if "from utils.premium import" not in txt:
    txt = txt.replace(
        "from utils.ui import aplicar_estilo_premium",
        "from utils.ui import aplicar_estilo_premium`nfrom utils.premium import aplicar_premium_goia, hero"
    )

txt = txt.replace(
    "aplicar_estilo_premium()",
    "aplicar_estilo_premium()`naplicar_premium_goia()",
    1
)

p.write_text(txt, encoding="utf-8")

print("Base Premium aplicada em Contas a Pagar.")
