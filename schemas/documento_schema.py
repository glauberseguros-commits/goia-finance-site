from dataclasses import dataclass

@dataclass
class DocumentoCreateDTO:
    empresa_id: int | None = None
    nome_arquivo: str = ""
    tipo_documento: str = ""
    origem: str = ""
    conteudo_texto: str = ""
