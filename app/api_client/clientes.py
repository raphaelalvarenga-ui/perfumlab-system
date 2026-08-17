from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.api_client.client import ApiClient


class ClientesApi:
    def __init__(self, api: ApiClient):
        self.api = api

    def listar(
        self,
        *,
        buscar: str | None = None,
        activo: bool | None = True,
        page: int = 1,
        limit: int = 100,
    ) -> dict:
        return self.api.request(
            "GET",
            "/api/v1/clientes",
            params={"buscar": buscar, "activo": activo, "page": page, "limit": limit},
        )

    def listar_todos(
        self,
        *,
        buscar: str | None = None,
        activo: bool | None = True,
    ) -> list[dict]:
        return self.api.get_all(
            "/api/v1/clientes",
            params={"buscar": buscar, "activo": activo},
        )

    def obtener(self, cliente_id: int) -> dict:
        return self.api.request("GET", f"/api/v1/clientes/{cliente_id}")

    def crear(self, data: dict) -> dict:
        return self.api.request("POST", "/api/v1/clientes", json=data)

    def actualizar(self, cliente_id: int, data: dict) -> dict:
        return self.api.request("PATCH", f"/api/v1/clientes/{cliente_id}", json=data)

    def eliminar(self, cliente_id: int) -> dict:
        return self.api.request("DELETE", f"/api/v1/clientes/{cliente_id}")
