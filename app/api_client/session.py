from __future__ import annotations

from dataclasses import dataclass


ADMIN_ROLE = "ADMINISTRADOR"
SELLER_ROLE = "VENDEDOR"


@dataclass
class UserSession:
    access_token: str | None = None
    usuario_id: int | None = None
    nombre: str = ""
    username: str = ""
    rol: str = ""
    activo: bool = False

    @property
    def is_authenticated(self) -> bool:
        return bool(self.access_token and self.usuario_id)

    @property
    def is_admin(self) -> bool:
        return self.rol == ADMIN_ROLE

    @property
    def is_vendedor(self) -> bool:
        return self.rol == SELLER_ROLE

    def set_token(self, token: str) -> None:
        self.access_token = token

    def set_user(self, user: dict) -> None:
        self.usuario_id = int(user["id"])
        self.nombre = str(user.get("nombre") or "")
        self.username = str(user.get("username") or "")
        self.rol = str(user.get("rol") or "")
        self.activo = bool(user.get("activo"))

    def clear(self) -> None:
        self.access_token = None
        self.usuario_id = None
        self.nombre = ""
        self.username = ""
        self.rol = ""
        self.activo = False


_USER_SESSION = UserSession()


def get_user_session() -> UserSession:
    return _USER_SESSION
