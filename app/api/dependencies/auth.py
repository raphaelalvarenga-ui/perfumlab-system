from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.api.routes._errors import service_error_to_http
from app.database.session import get_db
from app.models.orm.usuario import UsuarioORM
from app.models.tipos import RolUsuario
from app.services.auth_service import AuthService
from app.services.exceptions import ServiceError


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UsuarioORM:
    try:
        return AuthService(db).get_current_user(token)
    except ServiceError as error:
        raise service_error_to_http(error) from error


def require_roles(*roles: RolUsuario) -> Callable:
    allowed_roles = set(roles)

    def dependency(
        current_user: UsuarioORM = Depends(get_current_user),
    ) -> UsuarioORM:
        if current_user.rol not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta accion.",
            )
        return current_user

    return dependency
