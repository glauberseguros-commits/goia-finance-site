from pathlib import Path

p = Path("app.py")
txt = p.read_text(encoding="utf-8")

old = '''    st.markdown("## GOIA Finance Platform")
    st.subheader("Acesso ao sistema")
    st.caption("Entre com seu usuário para acessar as empresas vinculadas à sua assinatura.")

    with st.form("form_login"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")'''

new = '''    st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="stHeader"] {background: transparent;}
        .block-container {
            max-width: 1180px;
            padding-top: 60px;
        }
        .login-hero {
            background: linear-gradient(135deg, #050816 0%, #111827 55%, #172554 100%);
            border-radius: 28px;
            padding: 48px;
            color: white;
            margin-bottom: 28px;
            box-shadow: 0 24px 70px rgba(15, 23, 42, 0.22);
        }
        .login-kicker {
            color: #2dd4bf;
            font-size: 13px;
            font-weight: 800;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            margin-bottom: 12px;
        }
        .login-title {
            font-size: 46px;
            font-weight: 900;
            line-height: 1.08;
            margin-bottom: 16px;
        }
        .login-text {
            color: #cbd5e1;
            font-size: 17px;
            max-width: 760px;
        }
        .login-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 24px;
            padding: 30px;
            box-shadow: 0 18px 50px rgba(15, 23, 42, 0.10);
        }
        .login-note {
            background: #f8fafc;
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            padding: 22px;
            color: #475569;
            font-size: 14px;
        }
    </style>

    <div class="login-hero">
        <div class="login-kicker">GOIA Finance Platform</div>
        <div class="login-title">Inteligência financeira para empresas document-driven.</div>
        <div class="login-text">
            Acesse sua empresa, importe documentos, cadastre clientes e fornecedores,
            acompanhe contas, conciliações, pendências e caixa em um único ambiente.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_login, col_info = st.columns([1, 1])

    with col_login:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.subheader("Entrar na GOIA")

        with st.form("form_login"):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar")

        st.markdown("</div>", unsafe_allow_html=True)

    with col_info:
        st.markdown("""
        <div class="login-note">
            <b>Cliente assinante</b><br>
            A empresa acessa somente os próprios clientes, fornecedores, documentos,
            contas, bancos, conciliações e processos.<br><br>
            <b>Admin GOIA</b><br>
            Gerencia empresas assinantes, usuários, planos e suporte da plataforma.
        </div>
        """, unsafe_allow_html=True)'''

if old not in txt:
    raise SystemExit("Bloco de login não encontrado. Não alterei o arquivo.")

txt = txt.replace(old, new)

p.write_text(txt, encoding="utf-8")
print("OK - login premium aplicado.")
