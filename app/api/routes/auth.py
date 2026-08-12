from fastapi import APIRouter, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.routes._errors import service_error_to_http
from app.database.session import get_db
from app.models.orm.usuario import UsuarioORM
from app.schemas.auth import ChangePasswordRequest, TokenResponse
from app.schemas.usuario import UsuarioResponse
from app.services.auth_service import AuthService
from app.services.exceptions import ServiceError


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    try:
        token = AuthService(db).login(form_data.username, form_data.password)
        return TokenResponse(access_token=token)
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.get("/me", response_model=UsuarioResponse)
def obtener_usuario_actual(current_user: UsuarioORM = Depends(get_current_user)):
    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def cambiar_mi_password(
    payload: ChangePasswordRequest,
    current_user: UsuarioORM = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        AuthService(db).change_password(
            current_user,
            password_actual=payload.password_actual,
            password_nueva=payload.password_nueva,
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ServiceError as error:
        raise service_error_to_http(error) from error
