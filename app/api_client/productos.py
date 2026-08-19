from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.api_client.client import ApiClient


class ProductosApi:
    def __init__(self, api: ApiClient):
        self.api = api

    def listar(
        self,
        *,
        buscar: str | None = None,
        activo: bool | None = True,
        page: int = 1,
        limit: int = 100,
        **params: Any,
    ) -> dict:
        payload = {"buscar": buscar, "activo": activo, "page": page, "limit": limit}
        payload.update(params)
        return self.api.request("GET", "/api/v1/productos", params=payload)

    def listar_todos(
        self,
        *,
        buscar: str | None = None,
        activo: bool | None = True,
        **params: Any,
    ) -> list[dict]:
        payload = {"buscar": buscar, "activo": activo}
        payload.update(params)
        return self.api.get_all("/api/v1/productos", params=payload)

    def obtener(self, producto_id: int) -> dict:
        return self.api.request("GET", f"/api/v1/productos/{producto_id}")

    def obtener_perfil_olfativo(self, producto_id: int) -> dict:
        return self.api.request(
            "GET",
            f"/api/v1/productos/{producto_id}/perfil-olfativo",
        )

    def crear(self, data: dict) -> dict:
        return self.api.request("POST", "/api/v1/productos", json=data)

    def actualizar(self, producto_id: int, data: dict) -> dict:
        return self.api.request("PATCH", f"/api/v1/productos/{producto_id}", json=data)

    def eliminar(self, producto_id: int) -> dict:
        return self.api.request("DELETE", f"/api/v1/productos/{producto_id}")
