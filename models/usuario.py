from dataclasses import dataclass
from typing import Optional

@dataclass
class Usuario:
    id: Optional[int] = None
    empresa_id: Optional[int] = None
    nome: str = ""
    email: str = ""
    perfil: str = ""
    ativo: bool = True
