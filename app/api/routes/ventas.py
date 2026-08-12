from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_roles
from app.api.routes._errors import service_error_to_http
from app.database.session import get_db
from app.models.orm.usuario import UsuarioORM
from app.models.tipos import EstadoVenta, RolUsuario
from app.schemas.venta import (
    VentaAnularRequest,
    VentaCreate,
    VentaListResponse,
    VentaResponse,
)
from app.services.exceptions import ServiceError
from app.services.ventas_service import VentasService


router = APIRouter(prefix="/ventas", tags=["Ventas"])
admin_required = require_roles(RolUsuario.ADMINISTRADOR)
vendedor_or_admin_required = require_roles(
    RolUsuario.ADMINISTRADOR,
    RolUsuario.VENDEDOR,
)


@router.post("", response_model=VentaResponse, status_code=status.HTTP_201_CREATED)
def crear_venta(
    payload: VentaCreate,
    db: Session = Depends(get_db),
    actor: UsuarioORM = Depends(vendedor_or_admin_required),
):
    try:
        return VentasService(db).registrar_venta(
            payload.model_dump(),
            usuario_id=actor.id,
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.get("", response_model=VentaListResponse)
def listar_ventas(
    cliente_id: int | None = Query(default=None, ge=1),
    estado: EstadoVenta | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _current_user: UsuarioORM = Depends(get_current_user),
):
    return VentasService(db).listar_ventas(
        cliente_id=cliente_id,
        estado=estado,
        desde=desde,
        hasta=hasta,
        page=page,
        limit=limit,
    )


@router.get("/{venta_id}", response_model=VentaResponse)
def obtener_venta(
    venta_id: int,
    db: Session = Depends(get_db),
    _current_user: UsuarioORM = Depends(get_current_user),
):
    try:
        return VentasService(db).obtener_venta(venta_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.post("/{venta_id}/anular", response_model=VentaResponse)
def anular_venta(
    venta_id: int,
    payload: VentaAnularRequest,
    db: Session = Depends(get_db),
    admin: UsuarioORM = Depends(admin_required),
):
    try:
        return VentasService(db).anular_venta(
            venta_id,
            payload.model_dump(),
            usuario_id=admin.id,
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error
