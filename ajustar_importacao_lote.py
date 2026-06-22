from pathlib import Path

p = Path("pages/1_Importar_Documento.py")
txt = p.read_text(encoding="utf-8")

txt = txt.replace(
    'st.warning(f"Arquivo {extensao.upper()} aceito. Processador específico ainda será implementado.")\n                    st.stop()',
    'st.warning(f"Arquivo {extensao.upper()} aceito. Processador específico ainda será implementado.")\n                    continue'
)

txt = txt.replace(
    'st.error(f"Formato não suportado: {extensao}")\n                    st.stop()',
    'st.error(f"Formato não suportado: {extensao}")\n                    continue'
)

p.write_text(txt, encoding="utf-8")

print("Importador ajustado para continuar processando os próximos arquivos.")
