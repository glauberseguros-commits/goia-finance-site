from werkzeug.security import generate_password_hash, check_password_hash

def gerar_hash(senha: str) -> str:
    return generate_password_hash(senha)

def validar_hash(senha: str, senha_hash: str) -> bool:
    return check_password_hash(senha_hash, senha)
