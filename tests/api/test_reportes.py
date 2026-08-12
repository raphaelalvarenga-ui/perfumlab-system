from datetime import date, timedelta


def crear_categoria(client, nombre="Reportes"):
    response = client.post("/api/v1/categorias", json={"nombre": nombre})
    assert response.status_code == 201
    return response.json()


def producto_payload(categoria_id, **overrides):
    data = {
        "sku": "REP-001",
        "nombre": "Producto Reporte",
        "marca": "Marca Reporte",
        "descripcion": "Producto temporal de reporte",
        "categoria_id": categoria_id,
        "costo": "50.00",
        "precio": "100.00",
        "stock_actual": 20,
        "stock_minimo": 1,
        "ml": 50,
        "genero": "Unisex",
    }
    data.update(overrides)
    return data


def crear_producto(
    client,
    *,
    sku="REP-001",
    nombre="Producto Reporte",
    marca="Marca Reporte",
    stock_actual=20,
    stock_minimo=1,
    precio="100.00",
):
    categoria = crear_categoria(client, f"Categoria {sku}")
    response = client.post(
        "/api/v1/productos",
        json=producto_payload(
            categoria["id"],
            sku=sku,
            nombre=nombre,
            marca=marca,
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
            precio=precio,
        ),
    )
    assert response.status_code == 201
    return response.json()


def crear_cliente(client, nombre="Cliente Reporte"):
    response = client.post("/api/v1/clientes", json={"nombre": nombre})
    assert response.status_code == 201
    return response.json()


def crear_venta(client, productos, cliente_id=None):
    payload = {"productos": productos}
    if cliente_id is not None:
        payload["cliente_id"] = cliente_id
    response = client.post("/api/v1/ventas", json=payload)
    assert response.status_code == 201
    return response.json()


def generar_factura(client, venta_id):
    response = client.post(f"/api/v1/ventas/{venta_id}/factura")
    assert response.status_code == 201
    return response.json()


def anular_venta(client, venta_id, motivo="Reporte de prueba"):
    response = client.post(
        f"/api/v1/ventas/{venta_id}/anular",
        json={"motivo": motivo},
    )
    assert response.status_code == 200
    return response.json()


def fecha_venta(venta):
    return date.fromisoformat(venta["created_at"][:10])


def test_resumen_sin_datos(client):
    response = client.get("/api/v1/reportes/resumen")

    assert response.status_code == 200
    data = response.json()
    assert data == {
        "periodo": {"desde": None, "hasta": None},
        "ventas_completadas": 0,
        "ventas_anuladas": 0,
        "ingresos_totales": "0.00",
        "ticket_promedio": "0.00",
        "unidades_vendidas": 0,
        "facturas_emitidas": 0,
        "facturas_anuladas": 0,
        "productos_stock_bajo": 0,
    }


def test_resumen_anulacion_factura_anulada_y_stock_bajo(client):
    producto = crear_producto(
        client,
        sku="REP-ANULA",
        nombre="Venta Anulable",
        stock_actual=10,
        precio="280.00",
    )
    crear_producto(
        client,
        sku="REP-STOCK",
        nombre="Stock Bajo",
        stock_actual=2,
        stock_minimo=5,
    )
    venta = crear_venta(client, [{"producto_id": producto["id"], "cantidad": 3}])
    generar_factura(client, venta["id"])

    response = client.get("/api/v1/reportes/resumen")
    assert response.status_code == 200
    data = response.json()
    assert data["ventas_completadas"] == 1
    assert data["ventas_anuladas"] == 0
    assert data["ingresos_totales"] == "840.00"
    assert data["ticket_promedio"] == "840.00"
    assert data["unidades_vendidas"] == 3
    assert data["facturas_emitidas"] == 1
    assert data["facturas_anuladas"] == 0
    assert data["productos_stock_bajo"] == 1

    anular_venta(client, venta["id"])

    response = client.get("/api/v1/reportes/resumen")
    assert response.status_code == 200
    data = response.json()
    assert data["ventas_completadas"] == 0
    assert data["ventas_anuladas"] == 1
    assert data["ingresos_totales"] == "0.00"
    assert data["ticket_promedio"] == "0.00"
    assert data["unidades_vendidas"] == 0
    assert data["facturas_emitidas"] == 0
    assert data["facturas_anuladas"] == 1
    assert data["productos_stock_bajo"] == 1


def test_resumen_varias_ventas_y_ticket_promedio(client):
    producto_a = crear_producto(client, sku="REP-TICKET-A", precio="100.00")
    producto_b = crear_producto(client, sku="REP-TICKET-B", precio="300.00")

    crear_venta(client, [{"producto_id": producto_a["id"], "cantidad": 5}])
    crear_venta(client, [{"producto_id": producto_b["id"], "cantidad": 1}])

    response = client.get("/api/v1/reportes/resumen")

    assert response.status_code == 200
    data = response.json()
    assert data["ventas_completadas"] == 2
    assert data["ventas_anuladas"] == 0
    assert data["ingresos_totales"] == "800.00"
    assert data["ticket_promedio"] == "400.00"
    assert data["unidades_vendidas"] == 6


def test_filtros_fecha_desde_hasta_y_hasta_incluye_dia(client):
    producto = crear_producto(client, sku="REP-FECHA", precio="100.00")
    venta = crear_venta(client, [{"producto_id": producto["id"], "cantidad": 1}])
    hoy = fecha_venta(venta)
    ayer = hoy - timedelta(days=1)
    manana = hoy + timedelta(days=1)

    response = client.get("/api/v1/reportes/resumen", params={"desde": hoy.isoformat()})
    assert response.status_code == 200
    assert response.json()["ventas_completadas"] == 1

    response = client.get("/api/v1/reportes/resumen", params={"hasta": hoy.isoformat()})
    assert response.status_code == 200
    assert response.json()["ventas_completadas"] == 1

    response = client.get(
        "/api/v1/reportes/resumen",
        params={"desde": hoy.isoformat(), "hasta": hoy.isoformat()},
    )
    assert response.status_code == 200
    assert response.json()["ventas_completadas"] == 1

    response = client.get(
        "/api/v1/reportes/resumen",
        params={"desde": manana.isoformat(), "hasta": manana.isoformat()},
    )
    assert response.status_code == 200
    assert response.json()["ventas_completadas"] == 0

    response = client.get(
        "/api/v1/reportes/resumen",
        params={"hasta": ayer.isoformat()},
    )
    assert response.status_code == 200
    assert response.json()["ventas_completadas"] == 0

    response = client.get(
        "/api/v1/reportes/resumen",
        params={"desde": manana.isoformat(), "hasta": hoy.isoformat()},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "La fecha desde no puede ser mayor que hasta."


def test_ventas_agrupadas_dia_mes_y_multiproducto_sin_doble_conteo(client):
    producto_a = crear_producto(
        client,
        sku="REP-GRAF-A",
        nombre="Invictus",
        precio="100.00",
    )
    producto_b = crear_producto(
        client,
        sku="REP-GRAF-B",
        nombre="Sauvage",
        precio="200.00",
    )
    venta = crear_venta(
        client,
        [
            {"producto_id": producto_a["id"], "cantidad": 2},
            {"producto_id": producto_b["id"], "cantidad": 3},
        ],
    )
    venta_anulada = crear_venta(client, [{"producto_id": producto_a["id"], "cantidad": 1}])
    anular_venta(client, venta_anulada["id"])

    periodo_dia = fecha_venta(venta).isoformat()
    periodo_mes = periodo_dia[:7]

    response = client.get("/api/v1/reportes/ventas", params={"agrupar": "dia"})
    assert response.status_code == 200
    assert response.json() == {
        "agrupar": "dia",
        "items": [
            {
                "periodo": periodo_dia,
                "ventas": 1,
                "unidades": 5,
                "ingresos": "800.00",
            }
        ],
    }

    response = client.get("/api/v1/reportes/ventas", params={"agrupar": "mes"})
    assert response.status_code == 200
    assert response.json() == {
        "agrupar": "mes",
        "items": [
            {
                "periodo": periodo_mes,
                "ventas": 1,
                "unidades": 5,
                "ingresos": "800.00",
            }
        ],
    }

    response = client.get("/api/v1/reportes/ventas", params={"agrupar": "semana"})
    assert response.status_code == 400
    assert response.json()["detail"] == "El parametro agrupar debe ser dia o mes."


def test_productos_mas_vendidos_usa_snapshots_historicos_y_limit(client):
    producto_a = crear_producto(
        client,
        sku="REP-TOP-A",
        nombre="Perfume A",
        precio="100.00",
    )
    producto_b = crear_producto(
        client,
        sku="REP-TOP-B",
        nombre="Perfume B",
        precio="300.00",
    )
    crear_venta(
        client,
        [
            {"producto_id": producto_a["id"], "cantidad": 2},
            {"producto_id": producto_b["id"], "cantidad": 1},
        ],
    )
    crear_venta(client, [{"producto_id": producto_a["id"], "cantidad": 3}])
    venta_anulada = crear_venta(
        client,
        [{"producto_id": producto_b["id"], "cantidad": 10}],
    )
    anular_venta(client, venta_anulada["id"])

    response = client.patch(
        f"/api/v1/productos/{producto_a['id']}",
        json={"nombre": "Perfume A Renombrado", "precio": "999.00"},
    )
    assert response.status_code == 200

    response = client.get(
        "/api/v1/reportes/productos-mas-vendidos",
        params={"limit": 1},
    )
    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "producto_id": producto_a["id"],
                "producto_sku": "REP-TOP-A",
                "producto_nombre": "Perfume A",
                "unidades_vendidas": 5,
                "ingresos": "500.00",
            }
        ]
    }

    response = client.get("/api/v1/reportes/productos-mas-vendidos")
    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["producto_id"] for item in items] == [producto_a["id"], producto_b["id"]]
    assert items[1]["unidades_vendidas"] == 1
    assert items[1]["ingresos"] == "300.00"

    response = client.get(
        "/api/v1/reportes/productos-mas-vendidos",
        params={"limit": 0},
    )
    assert response.status_code == 422


def test_stock_bajo_filtra_ordena_y_pagina(client):
    producto_bajo = crear_producto(
        client,
        sku="REP-STOCK-BAJO",
        nombre="Bajo Mayor",
        marca="Marca Baja",
        stock_actual=2,
        stock_minimo=5,
    )
    producto_igual = crear_producto(
        client,
        sku="REP-STOCK-IGUAL",
        nombre="Igual Minimo",
        marca="Marca Baja",
        stock_actual=5,
        stock_minimo=5,
    )
    crear_producto(
        client,
        sku="REP-STOCK-OK",
        nombre="Stock Correcto",
        stock_actual=6,
        stock_minimo=5,
    )
    producto_inactivo = crear_producto(
        client,
        sku="REP-STOCK-INACT",
        nombre="Stock Inactivo",
        stock_actual=0,
        stock_minimo=5,
    )
    response = client.delete(f"/api/v1/productos/{producto_inactivo['id']}")
    assert response.status_code == 200

    response = client.get("/api/v1/reportes/stock-bajo", params={"page": 1, "limit": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["limit"] == 1
    assert data["total"] == 2
    assert data["pages"] == 2
    assert data["items"] == [
        {
            "producto_id": producto_bajo["id"],
            "sku": "REP-STOCK-BAJO",
            "nombre": "Bajo Mayor",
            "marca": "Marca Baja",
            "stock_actual": 2,
            "stock_minimo": 5,
            "faltante_minimo": 3,
        }
    ]

    response = client.get("/api/v1/reportes/stock-bajo", params={"page": 2, "limit": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["producto_id"] == producto_igual["id"]
    assert data["items"][0]["faltante_minimo"] == 0

    response = client.get("/api/v1/reportes/stock-bajo", params={"limit": 101})
    assert response.status_code == 422
