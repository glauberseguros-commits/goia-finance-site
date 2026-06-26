from dataclasses import dataclass
from typing import Optional

@dataclass
class Fornecedor:
    id: Optional[int] = None
    empresa_id: Optional[int] = None
    nome: str = ""
    cpf_cnpj: str = ""
    email: str = ""
    telefone: str = ""
