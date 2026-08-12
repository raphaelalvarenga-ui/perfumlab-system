from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_roles
from app.api.routes._errors import service_error_to_http
from app.database.session import get_db
from app.models.orm.usuario import UsuarioORM
from app.models.tipos import RolUsuario
from app.schemas.nota import NotaCreate, NotaListResponse, NotaResponse, NotaUpdate
from app.services.exceptions import ServiceError
from app.services.notas_service import NotasService


router = APIRouter(prefix="/notas", tags=["Notas"])
admin_required = require_roles(RolUsuario.ADMINISTRADOR)


@router.get("", response_model=NotaListResponse)
def listar_notas(
    buscar: str | None = None,
    activo: bool | None = True,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _current_user: UsuarioORM = Depends(get_current_user),
):
    return NotasService(db).listar_notas(
        buscar=buscar,
        activo=activo,
        page=page,
        limit=limit,
    )


@router.get("/{nota_id}", response_model=NotaResponse)
def obtener_nota(
    nota_id: int,
    db: Session = Depends(get_db),
    _current_user: UsuarioORM = Depends(get_current_user),
):
    try:
        return NotasService(db).obtener_nota(nota_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.post("", response_model=NotaResponse, status_code=status.HTTP_201_CREATED)
def crear_nota(
    payload: NotaCreate,
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return NotasService(db).crear_nota(payload.model_dump())
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.patch("/{nota_id}", response_model=NotaResponse)
def actualizar_nota(
    nota_id: int,
    payload: NotaUpdate,
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return NotasService(db).actualizar_nota(
            nota_id,
            payload.model_dump(exclude_unset=True),
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.delete("/{nota_id}", response_model=NotaResponse)
def eliminar_nota(
    nota_id: int,
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return NotasService(db).eliminar_nota(nota_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error
