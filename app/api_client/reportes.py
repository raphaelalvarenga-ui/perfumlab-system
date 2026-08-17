from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.api_client.client import ApiClient


class ReportesApi:
    def __init__(self, api: ApiClient):
        self.api = api

    def resumen(self, *, desde: str | None = None, hasta: str | None = None) -> dict:
        return self.api.request(
            "GET",
            "/api/v1/reportes/resumen",
            params={"desde": desde, "hasta": hasta},
        )

    def ventas(
        self,
        *,
        desde: str | None = None,
        hasta: str | None = None,
        agrupar: str = "dia",
    ) -> dict:
        return self.api.request(
            "GET",
            "/api/v1/reportes/ventas",
            params={"desde": desde, "hasta": hasta, "agrupar": agrupar},
        )

    def productos_mas_vendidos(
        self,
        *,
        desde: str | None = None,
        hasta: str | None = None,
        limit: int = 10,
    ) -> dict:
        return self.api.request(
            "GET",
            "/api/v1/reportes/productos-mas-vendidos",
            params={"desde": desde, "hasta": hasta, "limit": limit},
        )

    def stock_bajo(self, *, page: int = 1, limit: int = 100) -> dict:
        return self.api.request(
            "GET",
            "/api/v1/reportes/stock-bajo",
            params={"page": page, "limit": limit},
        )

    def stock_bajo_todo(self) -> list[dict]:
        return self.api.get_all("/api/v1/reportes/stock-bajo")
