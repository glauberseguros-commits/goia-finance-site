from pathlib import Path

p = Path("app.py")
txt = p.read_text(encoding="utf-8")

if "import hashlib" not in txt:
    txt = txt.replace("import streamlit as st", "import streamlit as st\nimport sqlite3\nimport hashlib")

auth_code = r'''

# =========================
# LOGIN / MULTIEMPRESA
# =========================

AUTH_DB_PATH = "bd/gofinance.db"

def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def buscar_usuario(email, senha):
    conn = sqlite3.connect(AUTH_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nome, email
        FROM usuarios
        WHERE email = ?
          AND senha_hash = ?
          AND ativo = 1
    """, (email.strip().lower(), hash_senha(senha)))

    usuario = cur.fetchone()

    if not usuario:
        conn.close()
        return None, []

    cur.execute("""
        SELECT e.id, e.nome, e.cnpj_cpf, ue.perfil_empresa
        FROM usuario_empresas ue
        JOIN empresas e ON e.id = ue.empresa_id
        WHERE ue.usuario_id = ?
          AND ue.ativo = 1
          AND COALESCE(e.status_assinatura, 'Ativa') = 'Ativa'
        ORDER BY e.nome
    """, (usuario["id"],))

    empresas = cur.fetchall()
    conn.close()

    return dict(usuario), [dict(e) for e in empresas]

def exigir_login():
    if st.session_state.get("logado") and st.session_state.get("empresa_id"):
        return

    st.markdown("## GOIA Finance Platform")
    st.subheader("Acesso ao sistema")
    st.caption("Entre com seu usuário para acessar as empresas vinculadas à sua assinatura.")

    with st.form("form_login"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        usuario, empresas = buscar_usuario(email, senha)

        if not usuario:
            st.error("Usuário ou senha inválidos.")
            st.stop()

        if not empresas:
            st.error("Usuário sem empresa vinculada.")
            st.stop()

        st.session_state["logado"] = True
        st.session_state["usuario_id"] = usuario["id"]
        st.session_state["usuario_nome"] = usuario["nome"]

        if len(empresas) == 1:
            st.session_state["empresa_id"] = empresas[0]["id"]
            st.session_state["empresa_nome"] = empresas[0]["nome"]
            st.rerun()

        st.session_state["empresas_usuario"] = empresas
        st.rerun()

    if st.session_state.get("logado") and not st.session_state.get("empresa_id"):
        empresas = st.session_state.get("empresas_usuario", [])
        nomes = [e["nome"] for e in empresas]
        escolhida = st.selectbox("Selecione a empresa", nomes)

        if st.button("Acessar empresa"):
            empresa = next(e for e in empresas if e["nome"] == escolhida)
            st.session_state["empresa_id"] = empresa["id"]
            st.session_state["empresa_nome"] = empresa["nome"]
            st.rerun()

    st.stop()

exigir_login()

'''

if "def exigir_login():" not in txt:
    idx = txt.find("st.set_page_config(")
    fim = txt.find("\n)", idx) + 2
    txt = txt[:fim] + auth_code + txt[fim:]

p.write_text(txt, encoding="utf-8")
print("OK - tela de login adicionada antes do dashboard.")
