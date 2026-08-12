from app.core.config import get_settings
from app.integrations.fragella_provider import FragellaProvider
from app.integrations.perfume_provider import PerfumeProvider, ProviderNotConfiguredError


def get_perfume_provider() -> PerfumeProvider:
    settings = get_settings()
    provider_name = settings.perfume_provider.strip().lower()
    if provider_name == "fragella":
        return FragellaProvider()
    raise ProviderNotConfiguredError(
        "Proveedor externo de perfumes no configurado."
    )
