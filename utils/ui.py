
import streamlit as st

def aplicar_estilo_premium():
    st.markdown("""
    <style>
    [data-testid="stSidebarNav"] { display: none !important; }

    .stApp {
        background: linear-gradient(180deg, #f7f8fb 0%, #eef1f7 100%) !important;
    }

    section[data-testid="stSidebar"] {
        background: #eef1f7 !important;
        border-right: 1px solid #d8deea !important;
    }

    h1 {
        font-size: 2.6rem !important;
        font-weight: 900 !important;
        letter-spacing: -0.05em !important;
        color: #242637 !important;
    }

    h2, h3 {
        font-weight: 800 !important;
        letter-spacing: -0.03em !important;
        color: #242637 !important;
    }

    [data-testid="stMetric"],
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stForm"] {
        background: #ffffff !important;
        border: 1px solid #e1e6ef !important;
        border-radius: 20px !important;
        box-shadow: 0 14px 34px rgba(20, 27, 45, 0.07) !important;
    }

    [data-testid="stFileUploader"] section {
        background: #eef2f8 !important;
        border: 1px dashed #c4ccdc !important;
        border-radius: 18px !important;
    }

    .stDataFrame {
        background: #ffffff !important;
        border-radius: 18px !important;
        border: 1px solid #e1e6ef !important;
        padding: 8px !important;
    }

    .stAlert {
        border-radius: 16px !important;
        border: 1px solid rgba(20, 27, 45, 0.08) !important;
    }

    button {
        border-radius: 12px !important;
        font-weight: 800 !important;
    }

    input, textarea, select {
        border-radius: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)
