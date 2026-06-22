from pathlib import Path

p = Path("pages/8_Movimentos_Bancarios.py")
txt = p.read_text(encoding="utf-8")

if "from utils.premium import" not in txt:
    txt = txt.replace(
        "from utils.ui import aplicar_estilo_premium, moeda",
        "from utils.ui import aplicar_estilo_premium, moeda\nfrom utils.premium import aplicar_premium_goia, hero"
    )

txt = txt.replace(
    "aplicar_estilo_premium()",
    "aplicar_estilo_premium()\naplicar_premium_goia()",
    1
)

txt = txt.replace(
    '''st.title("🏦 Movimentos Bancários")
st.caption("Movimentos importados de extratos OFX para conferência, auditoria e conciliação financeira.")''',
    '''hero(
    "Movimentos Bancarios",
    "Central de auditoria financeira para extratos OFX, conciliacao bancaria e rastreabilidade de movimentacoes.",
    icone="🏦"
)'''
)

p.write_text(txt, encoding="utf-8")

print("Premium aplicado em Movimentos Bancarios.")
