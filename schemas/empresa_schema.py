from dataclasses import dataclass

@dataclass
class EmpresaCreateDTO:
    nome: str = ""
    nome_fantasia: str = ""
    cnpj: str = ""
    email: str = ""
    telefone: str = ""
    senha: str = ""
    plano: str = "Teste"
