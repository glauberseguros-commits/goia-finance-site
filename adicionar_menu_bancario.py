from pathlib import Path

p = Path("app.py")
txt = p.read_text(encoding="utf-8")

alvo = '''st.sidebar.page_link("pages/3_Contas_a_Pagar.py", label="Contas a Pagar", icon="💸")'''

novo = '''st.sidebar.page_link("pages/3_Contas_a_Pagar.py", label="Contas a Pagar", icon="💸")
st.sidebar.page_link("pages/8_Movimentos_Bancarios.py", label="Movimentos Bancários", icon="🏦")
st.sidebar.page_link("pages/8_Conciliacao_Bancaria.py", label="Conciliação Bancária", icon="⚖️")'''

txt = txt.replace(alvo, novo)

p.write_text(txt, encoding="utf-8")

print("Menu atualizado.")
