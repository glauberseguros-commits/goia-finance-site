from dataclasses import dataclass
from typing import Optional

@dataclass
class Documento:
    id: Optional[int] = None
    empresa_id: Optional[int] = None
    tipo: str = ""
    descricao: str = ""
    status: str = ""
