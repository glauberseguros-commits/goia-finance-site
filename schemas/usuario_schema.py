from dataclasses import dataclass

@dataclass
class UsuarioCreateDTO:
    empresa_id: int | None = None
    nome: str = ""
    email: str = ""
    senha: str = ""
    perfil: str = "admin"
