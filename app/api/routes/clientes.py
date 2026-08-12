from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.routes._errors import service_error_to_http
from app.database.session import get_db
from app.schemas.cliente import (
    ClienteCreate,
    ClienteListResponse,
    ClienteResponse,
    ClienteUpdate,
)
from app.services.clientes_service import ClientesService
from app.services.exceptions import ServiceError


router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("", response_model=ClienteListResponse)
def listar_clientes(
    buscar: str | None = None,
    activo: bool | None = True,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return ClientesService(db).listar_clientes(
        buscar=buscar,
        activo=activo,
        page=page,
        limit=limit,
    )


@router.get("/{cliente_id}", response_model=ClienteResponse)
def obtener_cliente(cliente_id: int, db: Session = Depends(get_db)):
    try:
        return ClientesService(db).obtener_cliente(cliente_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.post(
    "",
    response_model=ClienteResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_cliente(payload: ClienteCreate, db: Session = Depends(get_db)):
    try:
        return ClientesService(db).crear_cliente(payload.model_dump())
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.put("/{cliente_id}", response_model=ClienteResponse)
def actualizar_cliente(
    cliente_id: int,
    payload: ClienteCreate,
    db: Session = Depends(get_db),
):
    try:
        return ClientesService(db).actualizar_cliente(
            cliente_id,
            payload.model_dump(),
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.patch("/{cliente_id}", response_model=ClienteResponse)
def actualizar_cliente_parcial(
    cliente_id: int,
    payload: ClienteUpdate,
    db: Session = Depends(get_db),
):
    try:
        return ClientesService(db).actualizar_cliente_parcial(
            cliente_id,
            payload.model_dump(exclude_unset=True),
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.delete("/{cliente_id}", response_model=ClienteResponse)
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    try:
        return ClientesService(db).eliminar_cliente(cliente_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error
