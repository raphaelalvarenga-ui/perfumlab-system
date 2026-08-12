from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_roles
from app.api.routes._errors import service_error_to_http
from app.database.session import get_db
from app.models.orm.usuario import UsuarioORM
from app.models.tipos import RolUsuario
from app.schemas.reporte import (
    ProductosMasVendidosResponse,
    ReporteResumenResponse,
    ReporteVentasResponse,
    StockBajoResponse,
)
from app.services.exceptions import ServiceError
from app.services.reportes_service import ReportesService


router = APIRouter(prefix="/reportes", tags=["Reportes"])
admin_required = require_roles(RolUsuario.ADMINISTRADOR)


@router.get("/resumen", response_model=ReporteResumenResponse)
def obtener_resumen(
    desde: date | None = None,
    hasta: date | None = None,
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return ReportesService(db).obtener_resumen(desde=desde, hasta=hasta)
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.get("/ventas", response_model=ReporteVentasResponse)
def obtener_ventas(
    desde: date | None = None,
    hasta: date | None = None,
    agrupar: str = Query(default="dia"),
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return ReportesService(db).ventas_por_periodo(
            desde=desde,
            hasta=hasta,
            agrupar=agrupar,
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.get("/productos-mas-vendidos", response_model=ProductosMasVendidosResponse)
def obtener_productos_mas_vendidos(
    desde: date | None = None,
    hasta: date | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return ReportesService(db).productos_mas_vendidos(
            desde=desde,
            hasta=hasta,
            limit=limit,
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.get("/stock-bajo", response_model=StockBajoResponse)
def obtener_stock_bajo(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
):
    return ReportesService(db).stock_bajo(page=page, limit=limit)
