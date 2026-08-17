import pytest

from app.api_client import ApiValidationError

from .conftest import json_response


def movimiento_response(**overrides):
    data = {
        "id": 1,
        "producto_id": 10,
        "tipo": "ENTRADA",
        "cantidad": 3,
        "stock_anterior": 5,
        "stock_nuevo": 8,
        "motivo": "Prueba",
        "created_at": "2026-08-17T10:00:00Z",
    }
    data.update(overrides)
    return data


def test_entrada_salida_ajuste_e_historial(make_api_client):
    requests = []

    def handler(request):
        requests.append(request)
        if request.url.path.endswith("/entrada"):
            return json_response(201, movimiento_response(tipo="ENTRADA"))
        if request.url.path.endswith("/salida"):
            return json_response(201, movimiento_response(tipo="SALIDA"))
        if request.url.path.endswith("/ajuste"):
            return json_response(201, movimiento_response(tipo="AJUSTE"))
        return json_response(
            200,
            {
                "items": [movimiento_response()],
                "page": 1,
                "limit": 100,
                "total": 1,
                "pages": 1,
            },
        )

    client = make_api_client(handler)

    assert client.inventario.registrar_entrada(10, 3, "Entrada")["tipo"] == "ENTRADA"
    assert client.inventario.registrar_salida(10, 2, "Salida")["tipo"] == "SALIDA"
    assert client.inventario.registrar_ajuste(10, 8, "Ajuste")["tipo"] == "AJUSTE"
    assert client.inventario.listar_movimientos_todos(producto_id=10)[0]["id"] == 1
    assert requests[-1].url.params["producto_id"] == "10"


def test_stock_insuficiente_es_validation_error(make_api_client):
    client = make_api_client(
        lambda _request: json_response(
            400,
            {"detail": "No hay suficiente stock para el producto API."},
        )
    )

    with pytest.raises(ApiValidationError) as error:
        client.inventario.registrar_salida(10, 99, "Salida")

    assert "suficiente stock" in str(error.value)
