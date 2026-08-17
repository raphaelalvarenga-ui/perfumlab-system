from .conftest import json_response


def test_resumen_ventas_y_productos_mas_vendidos_params(make_api_client):
    requests = []

    def handler(request):
        requests.append(request)
        if request.url.path.endswith("/resumen"):
            return json_response(
                200,
                {
                    "periodo": {"desde": "2026-08-01", "hasta": "2026-08-31"},
                    "ventas_completadas": 1,
                    "ventas_anuladas": 0,
                    "ingresos_totales": "100.00",
                    "ticket_promedio": "100.00",
                    "unidades_vendidas": 1,
                    "facturas_emitidas": 1,
                    "facturas_anuladas": 0,
                    "productos_stock_bajo": 0,
                },
            )
        if request.url.path.endswith("/ventas"):
            return json_response(
                200,
                {
                    "agrupar": "mes",
                    "items": [
                        {
                            "periodo": "2026-08",
                            "ventas": 1,
                            "unidades": 1,
                            "ingresos": "100.00",
                        }
                    ],
                },
            )
        return json_response(
            200,
            {
                "items": [
                    {
                        "producto_id": 10,
                        "producto_sku": "API-001",
                        "producto_nombre": "Producto API",
                        "unidades_vendidas": 1,
                        "ingresos": "100.00",
                    }
                ]
            },
        )

    client = make_api_client(handler)

    assert client.reportes.resumen(desde="2026-08-01", hasta="2026-08-31")
    assert client.reportes.ventas(desde="2026-08-01", hasta="2026-08-31", agrupar="mes")
    assert client.reportes.productos_mas_vendidos(limit=5)
    assert requests[0].url.params["desde"] == "2026-08-01"
    assert requests[1].url.params["agrupar"] == "mes"
    assert requests[2].url.params["limit"] == "5"


def test_stock_bajo_usa_paginacion(make_api_client):
    requests = []

    def handler(request):
        requests.append(request)
        return json_response(
            200,
            {
                "items": [
                    {
                        "producto_id": 10,
                        "sku": "API-001",
                        "nombre": "Producto API",
                        "marca": "Marca",
                        "stock_actual": 1,
                        "stock_minimo": 5,
                        "faltante_minimo": 4,
                    }
                ],
                "page": 1,
                "limit": 100,
                "total": 1,
                "pages": 1,
            },
        )

    client = make_api_client(handler)

    assert client.reportes.stock_bajo_todo()[0]["producto_id"] == 10
    assert requests[0].url.params["page"] == "1"
    assert requests[0].url.params["limit"] == "100"
