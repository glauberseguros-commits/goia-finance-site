"""
Utilitários documentais da GOIA.

Centraliza normalização de texto, remoção de acentos,
limpeza numérica e formatação básica de CPF/CNPJ.
"""

import re
import unicodedata


def remover_acentos(valor):
    texto = str(valor or "")
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def somente_numeros(valor):
    return re.sub(r"\D", "", str(valor or ""))


def normalizar_linha_ocr(linha):
    linha = str(linha or "").strip()

    if not linha:
        return ""

    partes = linha.split()
    pequenos = [p for p in partes if len(p) <= 2]

    if len(partes) >= 4 and len(pequenos) / max(len(partes), 1) >= 0.70:
        return "".join(partes)

    return linha


def normalizar_texto_ocr(texto):
    linhas = []

    for linha in str(texto or "").splitlines():
        linhas.append(linha)
        linhas.append(normalizar_linha_ocr(linha))

    compacto_total = re.sub(r"\s+", "", str(texto or ""))

    return "\n".join(linhas) + "\n" + compacto_total


def texto_para_busca(texto):
    texto = str(texto or "")
    bruto = texto
    normalizado = normalizar_texto_ocr(texto)
    sem_acentos = remover_acentos(normalizado)
    compacto_sem_acentos = re.sub(r"\s+", "", sem_acentos)

    return f"{bruto}\n{normalizado}\n{sem_acentos}\n{compacto_sem_acentos}"


def formatar_documento(valor):
    nums = somente_numeros(valor)

    if len(nums) == 14:
        return f"{nums[:2]}.{nums[2:5]}.{nums[5:8]}/{nums[8:12]}-{nums[12:]}"

    if len(nums) == 11:
        return f"{nums[:3]}.{nums[3:6]}.{nums[6:9]}-{nums[9:]}"

    return str(valor or "")
