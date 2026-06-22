from pathlib import Path

p = Path("pages/1_Importar_Documento.py")
txt = p.read_text(encoding="utf-8")

if "from utils.premium import" not in txt:
    txt = txt.replace(
        "from utils.ui import aplicar_estilo_premium",
        "from utils.ui import aplicar_estilo_premium\nfrom utils.premium import aplicar_premium_goia, hero, menu_principal"
    )

txt = txt.replace(
    "aplicar_estilo_premium()",
    "aplicar_estilo_premium()\naplicar_premium_goia()",
    1
)

inicio_antigo = '''st.title("📄 Importar Documento Financeiro")
st.caption("Envie NF-e, nota de empenho, comprovantes, boletos, extratos e cadastros. A GOIA classifica e cria o fluxo financeiro.")'''

inicio_novo = '''hero(
    "Central de Documentos",
    "Envie NF-e, OFX, boletos, comprovantes, notas de empenho e documentos cadastrais. A GOIA identifica entidades, cria evidências, pendências e movimentações financeiras automaticamente.",
    icone="📄"
)'''

txt = txt.replace(inicio_antigo, inicio_novo)

menu_antigo = '''menu_goia()'''

menu_novo = '''menu_principal()'''

txt = txt.replace(menu_antigo, menu_novo)

p.write_text(txt, encoding="utf-8")

print("Premium aplicado na página de importação.")
