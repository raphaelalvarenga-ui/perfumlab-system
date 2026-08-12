from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.routes._errors import service_error_to_http
from app.database.session import get_db
from app.models.tipos import EstadoFactura
from app.schemas.factura import FacturaListResponse, FacturaResponse
from app.services.exceptions import ServiceError
from app.services.facturas_service import FacturasService


router = APIRouter(tags=["Facturas"])


@router.post(
    "/ventas/{venta_id}/factura",
    response_model=FacturaResponse,
    status_code=status.HTTP_201_CREATED,
)
def generar_factura(venta_id: int, db: Session = Depends(get_db)):
    try:
        return FacturasService(db).generar_factura(venta_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.get("/facturas", response_model=FacturaListResponse)
def listar_facturas(
    venta_id: int | None = Query(default=None, ge=1),
    estado: EstadoFactura | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    buscar: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return FacturasService(db).listar_facturas(
        venta_id=venta_id,
        estado=estado,
        desde=desde,
        hasta=hasta,
        buscar=buscar,
        page=page,
        limit=limit,
    )


@router.get("/facturas/numero/{numero}", response_model=FacturaResponse)
def obtener_factura_por_numero(numero: str, db: Session = Depends(get_db)):
    try:
        return FacturasService(db).obtener_por_numero(numero)
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.get("/facturas/{factura_id}", response_model=FacturaResponse)
def obtener_factura(factura_id: int, db: Session = Depends(get_db)):
    try:
        return FacturasService(db).obtener_factura(factura_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error
