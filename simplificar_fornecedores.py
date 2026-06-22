from pathlib import Path

p = Path("pages/10_Fornecedores.py")
txt = p.read_text(encoding="utf-8")

marcadores = [
    'st.divider()\nst.subheader("Histórico financeiro do fornecedor")',
    'st.subheader("Histórico financeiro do fornecedor")'
]

pos = -1

for m in marcadores:
    pos = txt.find(m)
    if pos != -1:
        break

if pos == -1:
    raise SystemExit("Bloco de histórico financeiro do fornecedor não encontrado.")

novo_final = '''
st.divider()

st.caption("Versão 0.3 - Fornecedores")
'''

txt = txt[:pos].rstrip() + "\n\n" + novo_final

p.write_text(txt, encoding="utf-8")

print("Página Fornecedores simplificada com sucesso.")
