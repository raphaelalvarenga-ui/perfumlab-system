import json

from .conftest import json_response


def venta_response(**overrides):
    data = {
        "id": 20,
        "cliente_id": None,
        "cliente_nombre": "Cliente mostrador",
        "usuario_id": 1,
        "estado": "COMPLETADA",
        "subtotal": "40.00",
        "total": "40.00",
        "detalles": [],
        "created_at": "2026-08-17T10:00:00Z",
    }
    data.update(overrides)
    return data


def test_crear_venta_envia_solo_cliente_y_productos(make_api_client):
    captured = {}

    def handler(request):
        captured["payload"] = json.loads(request.content.decode())
        return json_response(201, venta_response())

    client = make_api_client(handler)

    venta = client.ventas.crear(
        cliente_id=None,
        productos=[{"producto_id": 1, "cantidad": 2}],
    )

    assert venta["id"] == 20
    assert captured["payload"] == {
        "cliente_id": None,
        "productos": [{"producto_id": 1, "cantidad": 2}],
    }
    assert "precio_unitario" not in captured["payload"]
    assert "subtotal" not in captured["payload"]
    assert "total" not in captured["payload"]
    assert "usuario_id" not in captured["payload"]
    assert "estado" not in captured["payload"]


def test_listar_obtener_y_anular_venta(make_api_client):
    requests = []

    def handler(request):
        requests.append(request)
        if request.method == "GET" and request.url.path == "/api/v1/ventas":
            return json_response(
                200,
                {
                    "items": [venta_response()],
                    "page": 1,
                    "limit": 100,
                    "total": 1,
                    "pages": 1,
                },
            )
        if request.method == "POST":
            return json_response(200, venta_response(estado="ANULADA"))
        return json_response(200, venta_response())

    client = make_api_client(handler)

    assert client.ventas.listar_todas(estado="COMPLETADA")[0]["id"] == 20
    assert client.ventas.obtener(20)["estado"] == "COMPLETADA"
    assert client.ventas.anular(20, "Cancelada")["estado"] == "ANULADA"
    assert requests[0].url.params["estado"] == "COMPLETADA"
    assert requests[-1].url.path == "/api/v1/ventas/20/anular"
