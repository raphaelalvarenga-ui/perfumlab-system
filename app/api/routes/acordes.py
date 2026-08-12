from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_roles
from app.api.routes._errors import service_error_to_http
from app.database.session import get_db
from app.models.orm.usuario import UsuarioORM
from app.models.tipos import RolUsuario
from app.schemas.acorde import AcordeCreate, AcordeListResponse, AcordeResponse, AcordeUpdate
from app.services.acordes_service import AcordesService
from app.services.exceptions import ServiceError


router = APIRouter(prefix="/acordes", tags=["Acordes"])
admin_required = require_roles(RolUsuario.ADMINISTRADOR)


@router.get("", response_model=AcordeListResponse)
def listar_acordes(
    buscar: str | None = None,
    activo: bool | None = True,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _current_user: UsuarioORM = Depends(get_current_user),
):
    return AcordesService(db).listar_acordes(
        buscar=buscar,
        activo=activo,
        page=page,
        limit=limit,
    )


@router.get("/{acorde_id}", response_model=AcordeResponse)
def obtener_acorde(
    acorde_id: int,
    db: Session = Depends(get_db),
    _current_user: UsuarioORM = Depends(get_current_user),
):
    try:
        return AcordesService(db).obtener_acorde(acorde_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.post("", response_model=AcordeResponse, status_code=status.HTTP_201_CREATED)
def crear_acorde(
    payload: AcordeCreate,
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return AcordesService(db).crear_acorde(payload.model_dump())
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.patch("/{acorde_id}", response_model=AcordeResponse)
def actualizar_acorde(
    acorde_id: int,
    payload: AcordeUpdate,
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return AcordesService(db).actualizar_acorde(
            acorde_id,
            payload.model_dump(exclude_unset=True),
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.delete("/{acorde_id}", response_model=AcordeResponse)
def eliminar_acorde(
    acorde_id: int,
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return AcordesService(db).eliminar_acorde(acorde_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error
