from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_roles
from app.api.routes._errors import service_error_to_http
from app.database.session import get_db
from app.models.orm.usuario import UsuarioORM
from app.models.tipos import RolUsuario
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioListResponse,
    UsuarioResetPasswordRequest,
    UsuarioResponse,
    UsuarioUpdate,
)
from app.services.exceptions import ServiceError
from app.services.usuarios_service import UsuariosService


router = APIRouter(prefix="/usuarios", tags=["Usuarios"])
admin_required = require_roles(RolUsuario.ADMINISTRADOR)


@router.post(
    "",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_usuario(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return UsuariosService(db).crear_usuario(payload.model_dump())
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.get("", response_model=UsuarioListResponse)
def listar_usuarios(
    buscar: str | None = None,
    rol: RolUsuario | None = None,
    activo: bool | None = True,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
):
    return UsuariosService(db).listar_usuarios(
        buscar=buscar,
        rol=rol,
        activo=activo,
        page=page,
        limit=limit,
    )


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return UsuariosService(db).obtener_usuario(usuario_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.patch("/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario(
    usuario_id: int,
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return UsuariosService(db).actualizar_usuario(
            usuario_id,
            payload.model_dump(exclude_unset=True),
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.delete("/{usuario_id}", response_model=UsuarioResponse)
def desactivar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return UsuariosService(db).desactivar_usuario(usuario_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.post("/{usuario_id}/reset-password", response_model=UsuarioResponse)
def reset_password_usuario(
    usuario_id: int,
    payload: UsuarioResetPasswordRequest,
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return UsuariosService(db).reset_password(usuario_id, payload.password_nueva)
    except ServiceError as error:
        raise service_error_to_http(error) from error
