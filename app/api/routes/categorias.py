from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.routes._errors import service_error_to_http
from app.database.session import get_db
from app.schemas.categoria import CategoriaCreate, CategoriaResponse, CategoriaUpdate
from app.services.categorias_service import CategoriasService
from app.services.exceptions import ServiceError


router = APIRouter(prefix="/categorias", tags=["Categorías"])


@router.get("", response_model=list[CategoriaResponse])
def listar_categorias(db: Session = Depends(get_db)):
    return CategoriasService(db).listar_categorias()


@router.get("/{categoria_id}", response_model=CategoriaResponse)
def obtener_categoria(categoria_id: int, db: Session = Depends(get_db)):
    try:
        return CategoriasService(db).obtener_categoria(categoria_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.post(
    "",
    response_model=CategoriaResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_categoria(payload: CategoriaCreate, db: Session = Depends(get_db)):
    try:
        return CategoriasService(db).crear_categoria(payload.model_dump())
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.put("/{categoria_id}", response_model=CategoriaResponse)
def actualizar_categoria(
    categoria_id: int,
    payload: CategoriaCreate,
    db: Session = Depends(get_db),
):
    try:
        return CategoriasService(db).actualizar_categoria(
            categoria_id,
            payload.model_dump(),
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.patch("/{categoria_id}", response_model=CategoriaResponse)
def actualizar_categoria_parcial(
    categoria_id: int,
    payload: CategoriaUpdate,
    db: Session = Depends(get_db),
):
    try:
        return CategoriasService(db).actualizar_categoria_parcial(
            categoria_id,
            payload.model_dump(exclude_unset=True),
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.delete("/{categoria_id}", response_model=CategoriaResponse)
def eliminar_categoria(categoria_id: int, db: Session = Depends(get_db)):
    try:
        return CategoriasService(db).eliminar_categoria(categoria_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error
