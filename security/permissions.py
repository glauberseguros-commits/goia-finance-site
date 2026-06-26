def possui_permissao(usuario: dict, permissao: str) -> bool:
    permissoes = usuario.get("permissoes", [])
    return permissao in permissoes or usuario.get("perfil") == "Administrador"
