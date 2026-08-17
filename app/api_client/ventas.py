from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.api_client.client import ApiClient


class VentasApi:
    def __init__(self, api: ApiClient):
        self.api = api

    def crear(self, *, cliente_id: int | None, productos: list[dict]) -> dict:
        return self.api.request(
            "POST",
            "/api/v1/ventas",
            json={"cliente_id": cliente_id, "productos": productos},
        )

    def listar(
        self,
        *,
        cliente_id: int | None = None,
        estado: str | None = None,
        desde: str | None = None,
        hasta: str | None = None,
        page: int = 1,
        limit: int = 100,
    ) -> dict:
        return self.api.request(
            "GET",
            "/api/v1/ventas",
            params={
                "cliente_id": cliente_id,
                "estado": estado,
                "desde": desde,
                "hasta": hasta,
                "page": page,
                "limit": limit,
            },
        )

    def listar_todas(
        self,
        *,
        cliente_id: int | None = None,
        estado: str | None = None,
        desde: str | None = None,
        hasta: str | None = None,
    ) -> list[dict]:
        return self.api.get_all(
            "/api/v1/ventas",
            params={
                "cliente_id": cliente_id,
                "estado": estado,
                "desde": desde,
                "hasta": hasta,
            },
        )

    def obtener(self, venta_id: int) -> dict:
        return self.api.request("GET", f"/api/v1/ventas/{venta_id}")

    def anular(self, venta_id: int, motivo: str) -> dict:
        return self.api.request(
            "POST",
            f"/api/v1/ventas/{venta_id}/anular",
            json={"motivo": motivo},
        )
