from pathlib import Path

p = Path("app.py")
txt = p.read_text(encoding="utf-8")

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
    'st.title("💰 GOIA Finance Platform")\nst.caption(f"Empresa ativa: {st.session_state.get(\'empresa_nome\')}")',
    'hero("Dashboard Executivo", f"Empresa ativa: {st.session_state.get(\'empresa_nome\')}", icone="💰")'
)

p.write_text(txt, encoding="utf-8")
print("Premium aplicado no Dashboard.")
