from pathlib import Path

arquivo = Path("app.py")
texto = arquivo.read_text(encoding="utf-8")

css = r'''
st.markdown("""
<style>
[data-testid="stSidebarNav"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)

'''

if '[data-testid="stSidebarNav"]' not in texto:
    texto = texto.replace(
        'st.set_page_config(\n    page_title="GOIA Finance Platform",\n    page_icon="💰",\n    layout="wide"\n)\n',
        'st.set_page_config(\n    page_title="GOIA Finance Platform",\n    page_icon="💰",\n    layout="wide"\n)\n\n' + css
    )

arquivo.write_text(texto, encoding="utf-8")
print("OK")
