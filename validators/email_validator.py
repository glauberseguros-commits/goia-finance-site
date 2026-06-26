import re

def email_valido(email):
    email = str(email or "").strip()
    if not email:
        return False
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email) is not None
