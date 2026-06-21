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


def menu_goia():
    st.sidebar.markdown("## GOIA")
    st.sidebar.page_link("app.py", label="Dashboard", icon="🏠")
    st.sidebar.page_link("pages/1_Importar_Documento.py", label="Importar Documento", icon="📄")
    st.sidebar.page_link("pages/9_Clientes.py", label="Clientes", icon="👥")
    st.sidebar.page_link("pages/10_Fornecedores.py", label="Fornecedores", icon="🏭")
    st.sidebar.page_link("pages/2_Contas_a_Receber.py", label="Contas a Receber", icon="💰")
    st.sidebar.page_link("pages/3_Contas_a_Pagar.py", label="Contas a Pagar", icon="💸")
    st.sidebar.page_link("pages/7_Processos_Documentais.py", label="Processos Documentais", icon="🗂️")
    st.sidebar.page_link("pages/8_Conciliacao_Bancaria.py", label="Conciliação Bancária", icon="🏦")

menu_goia()



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
