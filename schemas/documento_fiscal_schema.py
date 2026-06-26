from dataclasses import dataclass, field


@dataclass
class PessoaFiscalDTO:
    cnpj: str = ""
    cpf: str = ""
    nome: str = ""
    inscricao_estadual: str = ""


@dataclass
class ItemFiscalDTO:
    codigo: str = ""
    descricao: str = ""
    ncm: str = ""
    cfop: str = ""
    quantidade: float = 0.0
    valor_unitario: float = 0.0
    valor_total: float = 0.0


@dataclass
class DocumentoFiscalDTO:
    numero: str = ""
    serie: str = ""
    data_emissao: str = ""

    emitente: PessoaFiscalDTO = field(default_factory=PessoaFiscalDTO)
    destinatario: PessoaFiscalDTO = field(default_factory=PessoaFiscalDTO)

    valor_total: float = 0.0

    itens: list[ItemFiscalDTO] = field(default_factory=list)
