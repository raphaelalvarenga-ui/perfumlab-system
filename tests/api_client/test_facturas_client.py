from .conftest import json_response


def factura_response(**overrides):
    data = {
        "id": 30,
        "numero": "FAC-000020",
        "venta_id": 20,
        "usuario_id": 1,
        "cliente_nombre": "Cliente API",
        "subtotal": "40.00",
        "total": "40.00",
        "estado": "EMITIDA",
        "created_at": "2026-08-17T10:00:00Z",
        "detalles": [],
    }
    data.update(overrides)
    return data


def test_emitir_listar_obtener_y_buscar_por_numero(make_api_client):
    requests = []

    def handler(request):
        requests.append(request)
        if request.method == "POST":
            return json_response(201, factura_response())
        if request.url.path == "/api/v1/facturas":
            return json_response(
                200,
                {
                    "items": [factura_response()],
                    "page": 1,
                    "limit": 100,
                    "total": 1,
                    "pages": 1,
                },
            )
        return json_response(200, factura_response())

    client = make_api_client(handler)

    assert client.facturas.emitir(20)["numero"] == "FAC-000020"
    assert client.facturas.listar_todas(venta_id=20)[0]["id"] == 30
    assert client.facturas.obtener(30)["venta_id"] == 20
    assert client.facturas.obtener_por_numero("FAC-000020")["id"] == 30
    assert requests[0].url.path == "/api/v1/ventas/20/factura"
    assert requests[1].url.params["venta_id"] == "20"
