from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_roles
from app.api.routes._errors import service_error_to_http
from app.core.config import Settings, get_settings
from app.database.session import get_db
from app.integrations.factory import get_perfume_provider
from app.integrations.perfume_provider import PerfumeProvider
from app.models.orm.usuario import UsuarioORM
from app.models.tipos import RolUsuario
from app.schemas.proveedor_perfume import FragellaStatusResponse, FragellaUsageResponse
from app.services.exceptions import ServiceError
from app.services.proveedor_perfume_service import ProveedorPerfumeService


router = APIRouter(prefix="/integraciones", tags=["Integraciones"])
admin_required = require_roles(RolUsuario.ADMINISTRADOR)


@router.get("/fragella/status", response_model=FragellaStatusResponse)
def obtener_estado_fragella(
    settings: Settings = Depends(get_settings),
    _admin: UsuarioORM = Depends(admin_required),
):
    return FragellaStatusResponse(
        provider="fragella",
        configured=(
            settings.perfume_provider.strip().lower() == "fragella"
            and bool(settings.fragella_api_key and settings.fragella_api_key.strip())
        ),
    )


@router.get("/fragella/usage", response_model=FragellaUsageResponse)
def obtener_uso_fragella(
    db: Session = Depends(get_db),
    provider: PerfumeProvider = Depends(get_perfume_provider),
    _admin: UsuarioORM = Depends(admin_required),
):
    try:
        return ProveedorPerfumeService(db).obtener_usage(provider=provider)
    except ServiceError as error:
        raise service_error_to_http(error) from error
