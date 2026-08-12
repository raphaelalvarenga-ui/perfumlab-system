from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.routes._errors import service_error_to_http
from app.database.session import get_db
from app.models.tipos import TipoMovimientoInventario
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


@router.post(
    "/entrada",
    response_model=MovimientoInventarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_entrada(payload: InventarioEntrada, db: Session = Depends(get_db)):
    try:
        return InventarioService(db).registrar_entrada(payload.model_dump())
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.post(
    "/salida",
    response_model=MovimientoInventarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_salida(payload: InventarioSalida, db: Session = Depends(get_db)):
    try:
        return InventarioService(db).registrar_salida(payload.model_dump())
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.post(
    "/ajuste",
    response_model=MovimientoInventarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_ajuste(payload: InventarioAjuste, db: Session = Depends(get_db)):
    try:
        return InventarioService(db).registrar_ajuste(payload.model_dump())
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
def obtener_movimiento(movimiento_id: int, db: Session = Depends(get_db)):
    try:
        return InventarioService(db).obtener_movimiento(movimiento_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error
