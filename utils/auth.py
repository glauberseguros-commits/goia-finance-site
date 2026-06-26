import streamlit as st

from utils.repositories.empresas import empresa_ativa_existe, buscar_empresa_por_id


def limpar_sessao_usuario():
    chaves = [
        "logado",
        "empresa_id",
        "empresa_nome",
    ]

    for chave in chaves:
        st.session_state.pop(chave, None)


def validar_sessao_empresa():
    empresa_id = st.session_state.get("empresa_id")

    if not st.session_state.get("logado") or not empresa_id:
        limpar_sessao_usuario()
        return None

    if not empresa_ativa_existe(int(empresa_id)):
        limpar_sessao_usuario()
        return None

    empresa = buscar_empresa_por_id(int(empresa_id))

    if not empresa:
        limpar_sessao_usuario()
        return None

    st.session_state["empresa_nome"] = empresa.get("nome") or "Empresa"

    return int(empresa_id)
