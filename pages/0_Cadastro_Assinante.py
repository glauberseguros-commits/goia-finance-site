import streamlit as st

st.set_page_config(
    page_title="Cadastro de Assinante",
    page_icon="🏢",
    layout="wide"
)


st.markdown("""
<style>
[data-testid="stSidebarNav"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)


st.title("🏢 Criar Conta GOIA")
st.caption("Cadastre sua empresa para utilizar a plataforma.")

with st.form("cadastro_empresa"):

    cnpj = st.text_input("CNPJ")
    razao = st.text_input("Razão Social")
    fantasia = st.text_input("Nome Fantasia")

    nome_admin = st.text_input("Nome do Administrador")
    email = st.text_input("E-mail")
    telefone = st.text_input("Telefone")

    senha = st.text_input("Senha", type="password")
    confirmar = st.text_input("Confirmar Senha", type="password")

    enviar = st.form_submit_button("Criar Conta")

if enviar:

    if senha != confirmar:
        st.error("As senhas não conferem.")

    else:
        st.success(
            "Cadastro realizado. Próximo passo: gravar empresa, usuário e assinatura."
        )
