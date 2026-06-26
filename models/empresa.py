from dataclasses import dataclass
from typing import Optional

@dataclass
class Empresa:
    id: Optional[int] = None
    nome: str = ""
    nome_fantasia: str = ""
    cnpj: str = ""
    email: str = ""
    telefone: str = ""
    plano: str = "Teste"
    status_assinatura: str = "Teste"
