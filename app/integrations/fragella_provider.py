from app.core.config import get_settings
from app.integrations.perfume_provider import (
    ExternalFragrance,
    ProviderNotConfiguredError,
)


class FragellaProvider:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.fragella_api_key
        self.base_url = (base_url or settings.fragella_base_url).rstrip("/")

    def search_fragrances(
        self,
        nombre: str,
        marca: str | None = None,
    ) -> list[ExternalFragrance]:
        self._ensure_configured()
        raise NotImplementedError("Fragella sera conectado en una fase posterior.")

    def get_fragrance(self, external_id: str) -> ExternalFragrance:
        self._ensure_configured()
        raise NotImplementedError("Fragella sera conectado en una fase posterior.")

    def get_similar(self, nombre: str, limit: int = 10) -> list[ExternalFragrance]:
        self._ensure_configured()
        raise NotImplementedError("Fragella sera conectado en una fase posterior.")

    def _ensure_configured(self) -> None:
        if not self.api_key or not str(self.api_key).strip():
            raise ProviderNotConfiguredError(
                "Fragella no esta configurado. Define FRAGELLA_API_KEY."
            )
        if not self.base_url:
            raise ProviderNotConfiguredError(
                "Fragella no esta configurado. Define FRAGELLA_BASE_URL."
            )
