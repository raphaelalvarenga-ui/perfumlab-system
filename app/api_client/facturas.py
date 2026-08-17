from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.api_client.client import ApiClient


class FacturasApi:
    def __init__(self, api: ApiClient):
        self.api = api

    def emitir(self, venta_id: int) -> dict:
        return self.api.request("POST", f"/api/v1/ventas/{venta_id}/factura")

    def listar(
        self,
        *,
        venta_id: int | None = None,
        estado: str | None = None,
        buscar: str | None = None,
        desde: str | None = None,
        hasta: str | None = None,
        page: int = 1,
        limit: int = 100,
    ) -> dict:
        return self.api.request(
            "GET",
            "/api/v1/facturas",
            params={
                "venta_id": venta_id,
                "estado": estado,
                "buscar": buscar,
                "desde": desde,
                "hasta": hasta,
                "page": page,
                "limit": limit,
            },
        )

    def listar_todas(
        self,
        *,
        venta_id: int | None = None,
        estado: str | None = None,
        buscar: str | None = None,
        desde: str | None = None,
        hasta: str | None = None,
    ) -> list[dict]:
        return self.api.get_all(
            "/api/v1/facturas",
            params={
                "venta_id": venta_id,
                "estado": estado,
                "buscar": buscar,
                "desde": desde,
                "hasta": hasta,
            },
        )

    def obtener(self, factura_id: int) -> dict:
        return self.api.request("GET", f"/api/v1/facturas/{factura_id}")

    def obtener_por_numero(self, numero: str) -> dict:
        return self.api.request("GET", f"/api/v1/facturas/numero/{numero}")
