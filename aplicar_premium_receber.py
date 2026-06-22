from pathlib import Path

p = Path("pages/2_Contas_a_Receber.py")
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

antigo = '''st.title("💵 Contas a Receber")
st.caption("Recebimentos, títulos, clientes, documentos, baixas e rastreabilidade financeira.")'''

novo = '''hero(
    "Contas a Receber",
    "Gestao dos recebimentos, clientes, documentos fiscais, baixas e rastreabilidade financeira.",
    icone="GOIA"
)'''

txt = txt.replace(antigo, novo)

p.write_text(txt, encoding="utf-8")
print("Premium aplicado em Contas a Receber.")
