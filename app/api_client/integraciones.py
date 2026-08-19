from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.api_client.client import ApiClient


class IntegracionesApi:
    def __init__(self, api: ApiClient):
        self.api = api

    def fragella_usage(self) -> dict:
        return self.api.request("GET", "/api/v1/integraciones/fragella/usage")
