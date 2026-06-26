from dataclasses import dataclass
from typing import Optional

@dataclass
class Financeiro:
    id: Optional[int] = None
    empresa_id: Optional[int] = None
    tipo: str = ""
    descricao: str = ""
    valor: float = 0.0
    status: str = ""
