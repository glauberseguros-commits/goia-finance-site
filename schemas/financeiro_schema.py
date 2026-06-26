from dataclasses import dataclass

@dataclass
class FinanceiroCreateDTO:
    empresa_id: int | None = None
    tipo: str = ""
    descricao: str = ""
    categoria: str = ""
    valor: float = 0.0
    data_vencimento: str = ""
    status: str = "Pendente"
