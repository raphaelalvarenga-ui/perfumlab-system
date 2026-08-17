import httpx
import pytest

from app.api_client import (
    ApiAuthenticationError,
    ApiConflictError,
    ApiConnectionError,
    ApiNotFoundError,
    ApiPermissionError,
    ApiServerError,
    ApiValidationError,
)
from app.controllers import productos_controller
from app.controllers.productos_controller import ProductosController

from .conftest import json_response


@pytest.mark.parametrize(
    ("status_code", "exception_type"),
    [
        (400, ApiValidationError),
        (401, ApiAuthenticationError),
        (403, ApiPermissionError),
        (404, ApiNotFoundError),
        (409, ApiConflictError),
        (422, ApiValidationError),
        (500, ApiServerError),
        (503, ApiServerError),
    ],
)
def test_status_codes_map_to_local_exceptions(
    make_api_client,
    status_code,
    exception_type,
):
    client = make_api_client(
        lambda _request: json_response(status_code, {"detail": "Mensaje API"})
    )

    with pytest.raises(exception_type) as error:
        client.request("GET", "/api/v1/recurso")

    assert str(error.value)


def test_validation_detail_list_is_readable(make_api_client):
    client = make_api_client(
        lambda _request: json_response(
            422,
            {
                "detail": [
                    {
                        "loc": ["body", "sku"],
                        "msg": "Field required",
                    }
                ]
            },
        )
    )

    with pytest.raises(ApiValidationError) as error:
        client.request("POST", "/api/v1/productos", json={})

    assert "sku: Field required" in str(error.value)


def test_get_all_reads_paginated_payload(make_api_client):
    requests = []

    def handler(request):
        requests.append(request)
        page = int(request.url.params["page"])
        if page == 1:
            return json_response(
                200,
                {"items": [{"id": 1}], "page": 1, "limit": 1, "total": 2, "pages": 2},
            )
        return json_response(
            200,
            {"items": [{"id": 2}], "page": 2, "limit": 1, "total": 2, "pages": 2},
        )

    client = make_api_client(handler)

    assert client.get_all("/api/v1/productos", limit=1) == [{"id": 1}, {"id": 2}]
    assert [request.url.params["page"] for request in requests] == ["1", "2"]


def test_connection_error_does_not_fallback_to_json(make_api_client, monkeypatch):
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    client = make_api_client(handler)

    def fail_json(*_args, **_kwargs):
        raise AssertionError("No debe consultarse JSON cuando falla la API.")

    monkeypatch.setattr(productos_controller, "cargar_tabla", fail_json)
    controller = ProductosController(api_client=client)

    with pytest.raises(ApiConnectionError):
        controller.listar_productos()


def test_timeout_maps_to_connection_error(make_api_client):
    def handler(request):
        raise httpx.TimeoutException("timeout", request=request)

    client = make_api_client(handler)

    with pytest.raises(ApiConnectionError):
        client.request("GET", "/api/v1/health", auth_required=False)
