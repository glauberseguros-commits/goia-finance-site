from pathlib import Path

p = Path("pages/1_Importar_Documento.py")
txt = p.read_text(encoding="utf-8")

txt = txt.replace(
'''arquivos = st.file_uploader(
    "Anexar documentos PDF",
    type=["pdf"],
    accept_multiple_files=True
)''',
'''arquivos = st.file_uploader(
    "Anexar documentos",
    type=["pdf", "ofx", "csv", "txt", "xml"],
    accept_multiple_files=True
)'''
)

p.write_text(txt, encoding="utf-8")

print("Upload múltiplos formatos habilitado.")
