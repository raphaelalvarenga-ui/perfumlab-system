from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.routes._errors import service_error_to_http
from app.database.session import get_db
from app.schemas.producto import (
    ProductoCreate,
    ProductoListResponse,
    ProductoReplace,
    ProductoResponse,
    ProductoUpdate,
)
from app.services.exceptions import ServiceError
from app.services.productos_service import ProductosService


router = APIRouter(prefix="/productos", tags=["Productos"])


@router.get("", response_model=ProductoListResponse)
def listar_productos(
    buscar: str | None = None,
    marca: str | None = None,
    categoria_id: int | None = Query(default=None, ge=1),
    genero: str | None = None,
    activo: bool | None = True,
    stock_bajo: bool | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return ProductosService(db).listar_productos(
        buscar=buscar,
        marca=marca,
        categoria_id=categoria_id,
        genero=genero,
        activo=activo,
        stock_bajo=stock_bajo,
        page=page,
        limit=limit,
    )


@router.get("/{producto_id}", response_model=ProductoResponse)
def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    try:
        return ProductosService(db).obtener_producto(producto_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.post(
    "",
    response_model=ProductoResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_producto(payload: ProductoCreate, db: Session = Depends(get_db)):
    try:
        return ProductosService(db).crear_producto(payload.model_dump())
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.put("/{producto_id}", response_model=ProductoResponse)
def actualizar_producto(
    producto_id: int,
    payload: ProductoReplace,
    db: Session = Depends(get_db),
):
    try:
        return ProductosService(db).actualizar_producto(
            producto_id,
            payload.model_dump(),
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.patch("/{producto_id}", response_model=ProductoResponse)
def actualizar_producto_parcial(
    producto_id: int,
    payload: ProductoUpdate,
    db: Session = Depends(get_db),
):
    try:
        return ProductosService(db).actualizar_producto_parcial(
            producto_id,
            payload.model_dump(exclude_unset=True),
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.delete("/{producto_id}", response_model=ProductoResponse)
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    try:
        return ProductosService(db).eliminar_producto(producto_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error
