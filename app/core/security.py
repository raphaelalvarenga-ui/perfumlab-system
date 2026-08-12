from pwdlib import PasswordHash


password_hasher = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hasher.hash("dummy-password-for-login-check")


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def validate_password_policy(password: str) -> str:
    if password is None:
        raise ValueError("La contrasena es obligatoria.")
    if not isinstance(password, str):
        raise ValueError("La contrasena debe ser texto.")
    if len(password) < 8:
        raise ValueError("La contrasena debe tener al menos 8 caracteres.")
    if len(password) > 128:
        raise ValueError("La contrasena no puede superar 128 caracteres.")
    return password
