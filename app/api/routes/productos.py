from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user, require_roles
from app.api.routes._errors import service_error_to_http
from app.database.session import get_db
from app.integrations.factory import get_perfume_provider
from app.integrations.perfume_provider import PerfumeProvider
from app.models.orm.usuario import UsuarioORM
from app.models.tipos import RolUsuario, TipoNota
from app.schemas.perfumeria import PerfilOlfativoResponse, PerfilOlfativoUpdate
from app.schemas.proveedor_perfume import (
    ExternalFragranceResponse,
    ProductoProveedorCandidatosResponse,
    ProductoSimilaresResponse,
    SincronizarProveedorRequest,
    SincronizarProveedorResponse,
)
from app.schemas.producto import (
    ProductoCreate,
    ProductoListResponse,
    ProductoReplace,
    ProductoResponse,
    ProductoUpdate,
)
from app.services.exceptions import ServiceError
from app.services.perfumeria_service import PerfumeriaService
from app.services.productos_service import ProductosService
from app.services.proveedor_perfume_service import ProveedorPerfumeService


router = APIRouter(prefix="/productos", tags=["Productos"])
admin_required = require_roles(RolUsuario.ADMINISTRADOR)


@router.get("", response_model=ProductoListResponse)
def listar_productos(
    buscar: str | None = None,
    marca: str | None = None,
    categoria_id: int | None = Query(default=None, ge=1),
    genero: str | None = None,
    activo: bool | None = True,
    stock_bajo: bool | None = None,
    acorde: str | None = None,
    nota: str | None = None,
    tipo_nota: TipoNota | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _current_user: UsuarioORM = Depends(get_current_user),
):
    return ProductosService(db).listar_productos(
        buscar=buscar,
        marca=marca,
        categoria_id=categoria_id,
        genero=genero,
        activo=activo,
        stock_bajo=stock_bajo,
        acorde=acorde,
        nota=nota,
        tipo_nota=tipo_nota,
        page=page,
        limit=limit,
    )


@router.get("/{producto_id}/perfil-olfativo", response_model=PerfilOlfativoResponse)
def obtener_perfil_olfativo(
    producto_id: int,
    db: Session = Depends(get_db),
    _current_user: UsuarioORM = Depends(get_current_user),
):
    try:
        return PerfumeriaService(db).obtener_perfil(producto_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.put("/{producto_id}/perfil-olfativo", response_model=PerfilOlfativoResponse)
def reemplazar_perfil_olfativo(
    producto_id: int,
    payload: PerfilOlfativoUpdate,
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return PerfumeriaService(db).reemplazar_perfil(
            producto_id,
            payload.model_dump(),
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.get(
    "/{producto_id}/proveedor/candidatos",
    response_model=ProductoProveedorCandidatosResponse,
    tags=["Integraciones"],
)
def listar_candidatos_proveedor(
    producto_id: int,
    limit: int = Query(default=5, ge=1, le=10),
    db: Session = Depends(get_db),
    provider: PerfumeProvider = Depends(get_perfume_provider),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return ProveedorPerfumeService(db).listar_candidatos(
            producto_id,
            provider=provider,
            limit=limit,
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.get(
    "/{producto_id}/proveedor/candidatos/{external_id}",
    response_model=ExternalFragranceResponse,
    tags=["Integraciones"],
)
def obtener_preview_proveedor(
    producto_id: int,
    external_id: str,
    db: Session = Depends(get_db),
    provider: PerfumeProvider = Depends(get_perfume_provider),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return ProveedorPerfumeService(db).obtener_preview(
            producto_id,
            external_id=external_id,
            provider=provider,
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.post(
    "/{producto_id}/sincronizar-proveedor",
    response_model=SincronizarProveedorResponse,
    tags=["Integraciones"],
)
def sincronizar_producto_proveedor(
    producto_id: int,
    payload: SincronizarProveedorRequest,
    db: Session = Depends(get_db),
    provider: PerfumeProvider = Depends(get_perfume_provider),
    admin: UsuarioORM = Depends(admin_required),
):
    try:
        return ProveedorPerfumeService(db).sincronizar_producto(
            producto_id,
            external_id=payload.external_id,
            provider=provider,
            usuario_id=admin.id,
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.get(
    "/{producto_id}/similares",
    response_model=ProductoSimilaresResponse,
    tags=["Integraciones"],
)
def listar_similares_producto(
    producto_id: int,
    limit: int = Query(default=5, ge=1, le=10),
    db: Session = Depends(get_db),
    provider: PerfumeProvider = Depends(get_perfume_provider),
    _current_user: UsuarioORM = Depends(get_current_user),
):
    try:
        return ProveedorPerfumeService(db).listar_similares(
            producto_id,
            provider=provider,
            limit=limit,
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.get("/{producto_id}", response_model=ProductoResponse)
def obtener_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    _current_user: UsuarioORM = Depends(get_current_user),
):
    try:
        return ProductosService(db).obtener_producto(producto_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.post(
    "",
    response_model=ProductoResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_producto(
    payload: ProductoCreate,
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return ProductosService(db).crear_producto(payload.model_dump())
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.put("/{producto_id}", response_model=ProductoResponse)
def actualizar_producto(
    producto_id: int,
    payload: ProductoReplace,
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
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
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return ProductosService(db).actualizar_producto_parcial(
            producto_id,
            payload.model_dump(exclude_unset=True),
        )
    except ServiceError as error:
        raise service_error_to_http(error) from error


@router.delete("/{producto_id}", response_model=ProductoResponse)
def eliminar_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return ProductosService(db).eliminar_producto(producto_id)
    except ServiceError as error:
        raise service_error_to_http(error) from error
