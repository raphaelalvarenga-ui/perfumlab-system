from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.api_client.client import ApiClient


class CategoriasApi:
    def __init__(self, api: ApiClient):
        self.api = api

    def listar(self) -> list[dict]:
        return self.api.request("GET", "/api/v1/categorias")

    def obtener(self, categoria_id: int) -> dict:
        return self.api.request("GET", f"/api/v1/categorias/{categoria_id}")

    def crear(self, data: dict) -> dict:
        return self.api.request("POST", "/api/v1/categorias", json=data)

    def actualizar(self, categoria_id: int, data: dict) -> dict:
        return self.api.request("PATCH", f"/api/v1/categorias/{categoria_id}", json=data)

    def eliminar(self, categoria_id: int) -> dict:
        return self.api.request("DELETE", f"/api/v1/categorias/{categoria_id}")
