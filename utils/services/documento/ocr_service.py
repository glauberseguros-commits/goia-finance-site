"""
Serviço de extração de texto documental.

Responsável por extrair texto de PDFs usando:
1. pypdf para PDF pesquisável;
2. OCR com pdf2image + pytesseract quando necessário.
"""

from pdf2image import convert_from_bytes
from pypdf import PdfReader
import pytesseract


def extrair_texto_pypdf(arquivo):
    arquivo.seek(0)
    reader = PdfReader(arquivo)

    texto = ""

    for page in reader.pages:
        texto += page.extract_text() or ""
        texto += "\n"

    return texto.strip()


def extrair_texto_ocr(arquivo, dpi=300, lang="por+eng"):
    arquivo.seek(0)
    imagens = convert_from_bytes(arquivo.read(), dpi=dpi)

    texto = ""

    for imagem in imagens:
        texto += pytesseract.image_to_string(imagem, lang=lang)
        texto += "\n"

    return texto.strip()


def extrair_texto_pdf(arquivo, limite_minimo_texto=80):
    texto = extrair_texto_pypdf(arquivo)

    if len(texto) < limite_minimo_texto:
        texto = extrair_texto_ocr(arquivo)

    return texto
