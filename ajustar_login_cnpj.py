from pathlib import Path

p = Path("app.py")
txt = p.read_text(encoding="utf-8")

txt = txt.replace(
    'email = st.text_input("E-mail")',
    'cnpj = st.text_input("CNPJ")'
)

txt = txt.replace(
    'st.caption("Entre com seu usuário para acessar as empresas vinculadas à sua assinatura.")',
    'st.caption("Entre com o CNPJ e senha da empresa assinante.")'
)

txt = txt.replace(
    'if st.button("Entrar"):',
    '''col1, col2 = st.columns(2)

with col1:
    entrar = st.button("Entrar", use_container_width=True)

with col2:
    cadastrar = st.button("Criar Conta", use_container_width=True)

if cadastrar:
    st.switch_page("pages/0_Cadastro_Assinante.py")

if entrar:'''
)

p.write_text(txt, encoding="utf-8")
print("Login alterado para CNPJ.")
