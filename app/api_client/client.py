from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx

from app.api_client.exceptions import (
    ApiAuthenticationError,
    ApiConflictError,
    ApiConnectionError,
    ApiError,
    ApiNotFoundError,
    ApiPermissionError,
    ApiServerError,
    ApiValidationError,
    detail_to_message,
)
from app.api_client.session import UserSession, get_user_session
from app.desktop_config import get_desktop_config


class ApiClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        session: UserSession | None = None,
        transport: httpx.BaseTransport | None = None,
    ):
        configured_timeout = None
        if base_url is None:
            try:
                desktop_config = get_desktop_config()
            except ValueError as error:
                raise ApiConnectionError(str(error)) from error
            api_url = desktop_config.api_url
            configured_timeout = desktop_config.timeout_seconds
        else:
            api_url = base_url

        self.base_url = self._normalizar_base_url(api_url)
        self.timeout = timeout if timeout is not None else configured_timeout or 10.0
        self.session = session or get_user_session()
        self.on_authentication_error: Callable[[ApiAuthenticationError], None] | None = None
        self.http = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            transport=transport,
        )

        from app.api_client.auth import AuthClient
        from app.api_client.categorias import CategoriasApi
        from app.api_client.clientes import ClientesApi
        from app.api_client.facturas import FacturasApi
        from app.api_client.inventario import InventarioApi
        from app.api_client.productos import ProductosApi
        from app.api_client.reportes import ReportesApi
        from app.api_client.ventas import VentasApi

        self.auth = AuthClient(self)
        self.categorias = CategoriasApi(self)
        self.productos = ProductosApi(self)
        self.clientes = ClientesApi(self)
        self.inventario = InventarioApi(self)
        self.ventas = VentasApi(self)
        self.facturas = FacturasApi(self)
        self.reportes = ReportesApi(self)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        auth_required: bool = True,
    ) -> Any:
        headers = {}
        if auth_required and self.session.access_token:
            headers["Authorization"] = f"Bearer {self.session.access_token}"

        try:
            response = self.http.request(
                method,
                path,
                params=self._clean_params(params),
                json=json,
                data=data,
                headers=headers,
            )
        except httpx.TimeoutException as error:
            raise ApiConnectionError(
                "No se pudo conectar con Perfum Lab API dentro del tiempo esperado.",
            ) from error
        except httpx.RequestError as error:
            raise ApiConnectionError(
                "No se pudo conectar con Perfum Lab API. Verifique que el servidor este iniciado.",
            ) from error

        if response.status_code >= 400:
            self._raise_for_response(response)
        if response.status_code == 204:
            return None
        try:
            return response.json()
        except ValueError as error:
            raise ApiServerError(
                "La API devolvio una respuesta invalida.",
                status_code=response.status_code,
            ) from error

    def get_all(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        page = 1
        items: list[dict[str, Any]] = []
        while True:
            payload = dict(params or {})
            payload.update({"page": page, "limit": limit})
            data = self.request("GET", path, params=payload)
            if isinstance(data, list):
                return data
            page_items = data.get("items", [])
            items.extend(page_items)
            pages = int(data.get("pages") or 0)
            if page >= pages or not page_items:
                return items
            page += 1

    def health_check(self, *, include_db: bool = True) -> None:
        self.request("GET", "/api/v1/health", auth_required=False)
        if include_db:
            self.request("GET", "/api/v1/health/db", auth_required=False)

    def close(self) -> None:
        self.http.close()

    def _raise_for_response(self, response: httpx.Response) -> None:
        detail = _response_detail(response)
        status_code = response.status_code

        if status_code == 401:
            had_token = bool(self.session.access_token)
            mensaje = (
                "La sesion expiro. Inicie sesion nuevamente."
                if had_token
                else "Usuario o contrasena incorrectos."
            )
            error = ApiAuthenticationError(
                mensaje,
                status_code=status_code,
                detail=detail,
            )
            if had_token:
                self.session.clear()
                if self.on_authentication_error is not None:
                    self.on_authentication_error(error)
            raise error

        if status_code == 403:
            raise ApiPermissionError(
                "No tiene permisos para realizar esta operacion.",
                status_code=status_code,
                detail=detail,
            )
        if status_code == 404:
            raise ApiNotFoundError(
                detail_to_message(detail, fallback="El recurso no existe."),
                status_code=status_code,
                detail=detail,
            )
        if status_code == 409:
            raise ApiConflictError(
                detail_to_message(detail, fallback="Existe un conflicto con los datos enviados."),
                status_code=status_code,
                detail=detail,
            )
        if status_code in {400, 422}:
            raise ApiValidationError(
                detail_to_message(detail, fallback="Revise los datos ingresados."),
                status_code=status_code,
                detail=detail,
            )
        if status_code >= 500:
            raise ApiServerError(
                "Perfum Lab API no pudo completar la operacion.",
                status_code=status_code,
                detail=detail,
            )
        raise ApiError(
            detail_to_message(detail, fallback="La API rechazo la operacion."),
            status_code=status_code,
            detail=detail,
        )

    def _normalizar_base_url(self, value: str) -> str:
        texto = str(value or "").strip().rstrip("/")
        if not texto:
            raise ApiConnectionError("PERFUMLAB_API_URL no esta configurada.")
        if not texto.startswith(("http://", "https://")):
            raise ApiConnectionError(
                "PERFUMLAB_API_URL debe comenzar con http:// o https://.",
            )
        return texto

    def _clean_params(self, params: dict[str, Any] | None) -> dict[str, Any] | None:
        if params is None:
            return None
        return {key: value for key, value in params.items() if value is not None}


def _response_detail(response: httpx.Response) -> Any:
    try:
        data = response.json()
    except ValueError:
        return response.text
    if isinstance(data, dict) and "detail" in data:
        return data["detail"]
    return data


_API_CLIENT: ApiClient | None = None


def get_api_client() -> ApiClient:
    global _API_CLIENT
    if _API_CLIENT is None:
        _API_CLIENT = ApiClient()
    return _API_CLIENT


def reset_api_client() -> None:
    global _API_CLIENT
    if _API_CLIENT is not None:
        _API_CLIENT.close()
    _API_CLIENT = None
