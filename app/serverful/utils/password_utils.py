import bcrypt


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password cannot be empty")
    salt: bytes = bcrypt.gensalt()
    hashed: bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(hashed: str, plain: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, AttributeError):
        return False
