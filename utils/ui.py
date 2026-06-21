
import streamlit as st

def aplicar_estilo_premium():
    st.markdown("""
    <style>
    [data-testid="stSidebarNav"] { display: none; }

    .stApp {
        background: #f7f8fb;
    }

    section[data-testid="stSidebar"] {
        background: #eef1f7;
        border-right: 1px solid #d9deea;
    }

    h1 {
        font-size: 2.4rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.04em;
        color: #262838;
    }

    h2, h3 {
        color: #262838;
        font-weight: 750 !important;
        letter-spacing: -0.03em;
    }

    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #e3e7ef;
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 8px 24px rgba(25, 30, 55, 0.06);
    }

    [data-testid="stForm"],
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: white;
        border-radius: 18px;
        border: 1px solid #e3e7ef;
        box-shadow: 0 8px 24px rgba(25, 30, 55, 0.05);
    }

    .stDataFrame {
        background: white;
        border-radius: 16px;
        border: 1px solid #e3e7ef;
        padding: 8px;
    }

    div.stButton > button,
    button[kind="secondary"],
    button[kind="primary"] {
        border-radius: 12px !important;
        border: 1px solid #d9deea !important;
        font-weight: 700 !important;
        padding: 0.55rem 1rem !important;
    }

    div.stButton > button:hover {
        border-color: #111827 !important;
        color: #111827 !important;
    }

    [data-testid="stFileUploader"] section {
        background: #eef1f7;
        border-radius: 16px;
        border: 1px dashed #cbd3e3;
    }

    .stAlert {
        border-radius: 16px;
    }

    input, textarea, select {
        border-radius: 12px !important;
    }

    </style>
    """, unsafe_allow_html=True)
