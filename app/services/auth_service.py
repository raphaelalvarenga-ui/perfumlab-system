from datetime import datetime, timedelta, timezone

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import DUMMY_PASSWORD_HASH, hash_password, verify_password
from app.models.orm.usuario import UsuarioORM
from app.repositories.usuarios_repository import UsuariosRepository
from app.services.exceptions import ForbiddenError, UnauthorizedError


INVALID_CREDENTIALS = "Usuario o contrasena incorrectos."
INVALID_TOKEN = "No se pudo validar el token."


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UsuariosRepository(db)
        self.settings = get_settings()

    def login(self, username: str, password: str) -> str:
        usuario = self.repository.get_by_username(username.strip().lower())
        if usuario is None:
            verify_password(password, DUMMY_PASSWORD_HASH)
            raise UnauthorizedError(INVALID_CREDENTIALS)

        if not verify_password(password, usuario.password_hash):
            raise UnauthorizedError(INVALID_CREDENTIALS)
        if not usuario.activo:
            raise ForbiddenError("El usuario esta inactivo.")

        self.repository.set_last_login(usuario, self._utc_now())
        self.db.commit()
        self.db.refresh(usuario)
        return self.create_access_token(usuario)

    def create_access_token(self, usuario: UsuarioORM) -> str:
        now = self._utc_now()
        expires_at = now + timedelta(minutes=self.settings.access_token_expire_minutes)
        payload = {
            "sub": str(usuario.id),
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "ver": usuario.token_version,
        }
        return jwt.encode(
            payload,
            self.settings.secret_key,
            algorithm=self.settings.jwt_algorithm,
        )

    def get_current_user(self, token: str) -> UsuarioORM:
        payload = self._decode_token(token)
        sub = payload.get("sub")
        token_version = payload.get("ver")
        if sub is None or token_version is None:
            raise UnauthorizedError(INVALID_TOKEN)

        try:
            usuario_id = int(sub)
            token_version = int(token_version)
        except (TypeError, ValueError) as error:
            raise UnauthorizedError(INVALID_TOKEN) from error

        usuario = self.repository.get_by_id(usuario_id)
        if usuario is None or not usuario.activo:
            raise UnauthorizedError(INVALID_TOKEN)
        if token_version != usuario.token_version:
            raise UnauthorizedError(INVALID_TOKEN)
        return usuario

    def change_password(
        self,
        usuario: UsuarioORM,
        *,
        password_actual: str,
        password_nueva: str,
    ) -> None:
        usuario_actual = self.repository.get_by_id_for_update(usuario.id)
        if usuario_actual is None or not usuario_actual.activo:
            raise UnauthorizedError(INVALID_TOKEN)
        if not verify_password(password_actual, usuario_actual.password_hash):
            raise UnauthorizedError("La contrasena actual no es correcta.")

        self.repository.update_password_hash(usuario_actual, hash_password(password_nueva))
        self.db.commit()

    def _decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.jwt_algorithm],
            )
        except ExpiredSignatureError as error:
            raise UnauthorizedError("El token ha expirado.") from error
        except InvalidTokenError as error:
            raise UnauthorizedError(INVALID_TOKEN) from error

    def _utc_now(self) -> datetime:
        return datetime.now(timezone.utc)
