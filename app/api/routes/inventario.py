from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_roles
from app.api.routes._errors import service_error_to_http
from app.database.session import get_db
from app.models.orm.usuario import UsuarioORM
from app.models.tipos import TipoMovimientoInventario
from app.models.tipos import RolUsuario
from app.schemas.inventario import (
    InventarioAjuste,
    InventarioEntrada,
    InventarioSalida,
    MovimientoInventarioListResponse,
    MovimientoInventarioResponse,
)
from app.services.exceptions import ServiceError
from app.services.inventario_service import InventarioService


router = APIRouter(prefix="/inventario", tags=["Inventario"])
admin_required = require_roles(RolUsuario.ADMINISTRADOR)


@router.post(
    "/entrada",
    response_model=MovimientoInventarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_entrada(
    payload: InventarioEntrada,
    db: Session = Depends(get_db),
    admin: UsuarioORM = Depends(admin_required),
):
    try:
        return InventarioService(db).registrar_entrada(
            payload.model_dump(),
            usuario_id=admin.id,
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.post(
    "/salida",
    response_model=MovimientoInventarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_salida(
    payload: InventarioSalida,
    db: Session = Depends(get_db),
    admin: UsuarioORM = Depends(admin_required),
):
    try:
        return InventarioService(db).registrar_salida(
            payload.model_dump(),
            usuario_id=admin.id,
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.post(
    "/ajuste",
    response_model=MovimientoInventarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_ajuste(
    payload: InventarioAjuste,
    db: Session = Depends(get_db),
    admin: UsuarioORM = Depends(admin_required),
):
    try:
        return InventarioService(db).registrar_ajuste(
            payload.model_dump(),
            usuario_id=admin.id,
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.get(
    "/movimientos",
    response_model=MovimientoInventarioListResponse,
)
def listar_movimientos(
    producto_id: int | None = Query(default=None, ge=1),
    tipo: TipoMovimientoInventario | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _current_user: UsuarioORM = Depends(get_current_user),
):
    return InventarioService(db).listar_movimientos(
        producto_id=producto_id,
        tipo=tipo,
        desde=desde,
        hasta=hasta,
        page=page,
        limit=limit,
    )


@router.get(
    "/movimientos/{movimiento_id}",
    response_model=MovimientoInventarioResponse,
)
def obtener_movimiento(
    movimiento_id: int,
    db: Session = Depends(get_db),
    _current_user: UsuarioORM = Depends(get_current_user),
):
    try:
        return InventarioService(db).obtener_movimiento(movimiento_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error
