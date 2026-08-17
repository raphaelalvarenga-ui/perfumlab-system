from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.api_client.client import ApiClient


class InventarioApi:
    def __init__(self, api: ApiClient):
        self.api = api

    def registrar_entrada(self, producto_id: int, cantidad: int, motivo: str) -> dict:
        return self.api.request(
            "POST",
            "/api/v1/inventario/entrada",
            json={"producto_id": producto_id, "cantidad": cantidad, "motivo": motivo},
        )

    def registrar_salida(self, producto_id: int, cantidad: int, motivo: str) -> dict:
        return self.api.request(
            "POST",
            "/api/v1/inventario/salida",
            json={"producto_id": producto_id, "cantidad": cantidad, "motivo": motivo},
        )

    def registrar_ajuste(self, producto_id: int, stock_nuevo: int, motivo: str) -> dict:
        return self.api.request(
            "POST",
            "/api/v1/inventario/ajuste",
            json={"producto_id": producto_id, "stock_nuevo": stock_nuevo, "motivo": motivo},
        )

    def listar_movimientos(
        self,
        *,
        producto_id: int | None = None,
        tipo: str | None = None,
        page: int = 1,
        limit: int = 100,
    ) -> dict:
        return self.api.request(
            "GET",
            "/api/v1/inventario/movimientos",
            params={
                "producto_id": producto_id,
                "tipo": tipo,
                "page": page,
                "limit": limit,
            },
        )

    def listar_movimientos_todos(
        self,
        *,
        producto_id: int | None = None,
        tipo: str | None = None,
    ) -> list[dict]:
        return self.api.get_all(
            "/api/v1/inventario/movimientos",
            params={"producto_id": producto_id, "tipo": tipo},
        )

    def obtener_movimiento(self, movimiento_id: int) -> dict:
        return self.api.request("GET", f"/api/v1/inventario/movimientos/{movimiento_id}")
