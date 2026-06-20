import streamlit as st

def empresa_logada():
    return st.session_state.get("empresa_id")

def exigir_login():
    if "empresa_id" not in st.session_state:
        st.switch_page("app.py")
