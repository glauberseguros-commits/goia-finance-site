from pathlib import Path

p = Path("pages/8_Conciliacao_Bancaria.py")
txt = p.read_text(encoding="utf-8")

if "from utils.premium import" not in txt:
    txt = txt.replace(
        "from utils.ui import aplicar_estilo_premium",
        "from utils.ui import aplicar_estilo_premium\nfrom utils.premium import aplicar_premium_goia, hero"
    )

txt = txt.replace(
    "aplicar_estilo_premium()",
    "aplicar_estilo_premium()\naplicar_premium_goia()",
    1
)

txt = txt.replace(
    'st.title("Conciliação Bancária")',
    '''hero(
    "Conciliacao Bancaria",
    "Relacione automaticamente movimentacoes bancarias com contas a receber e contas a pagar.",
    icone="GOIA"
)'''
)

p.write_text(txt, encoding="utf-8")

print("Premium aplicado na conciliacao.")
