import sys
from getpass import getpass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app.models.orm  # noqa: F401
from app.database.session import SessionLocal
from app.models.tipos import RolUsuario
from app.schemas.usuario import UsuarioCreate
from app.services.exceptions import ServiceError
from app.services.usuarios_service import UsuariosService


def main() -> int:
    if SessionLocal is None:
        print("DATABASE_URL no esta configurado.")
        return 1

    print("Crear primer administrador de Perfum Lab")
    nombre = input("Nombre: ").strip()
    username = input("Username: ").strip()
    email_texto = input("Email opcional: ").strip()
    password = getpass("Contrasena: ")
    password_confirmacion = getpass("Confirmar contrasena: ")

    if password != password_confirmacion:
        print("Las contrasenas no coinciden.")
        return 1

    try:
        payload = UsuarioCreate(
            nombre=nombre,
            username=username,
            email=email_texto or None,
            password=password,
            rol=RolUsuario.ADMINISTRADOR,
            activo=True,
        )
    except Exception as error:
        print(f"Datos invalidos: {error}")
        return 1

    db = SessionLocal()
    try:
        usuario = UsuariosService(db).crear_usuario(payload.model_dump())
        print(f"Administrador creado: id={usuario.id}, username={usuario.username}")
        return 0
    except ServiceError as error:
        print(error.detail)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
