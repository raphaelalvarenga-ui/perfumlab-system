from datetime import datetime, timedelta, timezone


def crear_categoria(client, nombre="Ventas"):
    response = client.post("/api/v1/categorias", json={"nombre": nombre})
    assert response.status_code == 201
    return response.json()


def producto_payload(categoria_id, **overrides):
    data = {
        "sku": "SALE-001",
        "nombre": "Producto Venta",
        "marca": "Marca Venta",
        "descripcion": "Producto temporal de venta",
        "categoria_id": categoria_id,
        "costo": "100.00",
        "precio": "280.00",
        "stock_actual": 10,
        "stock_minimo": 1,
        "ml": 50,
        "genero": "Unisex",
    }
    data.update(overrides)
    return data


def crear_producto(
    client,
    *,
    sku="SALE-001",
    nombre="Producto Venta",
    stock_actual=10,
    precio="280.00",
):
    categoria = crear_categoria(client, f"Categoria {sku}")
    response = client.post(
        "/api/v1/productos",
        json=producto_payload(
            categoria["id"],
            sku=sku,
            nombre=nombre,
            stock_actual=stock_actual,
            precio=precio,
        ),
    )
    assert response.status_code == 201
    return response.json()


def crear_cliente(client, nombre="Cliente Venta", activo=True):
    response = client.post(
        "/api/v1/clientes",
        json={"nombre": nombre, "activo": activo},
    )
    assert response.status_code == 201
    return response.json()


def obtener_producto(client, producto_id):
    response = client.get(f"/api/v1/productos/{producto_id}")
    assert response.status_code == 200
    return response.json()


def crear_venta(client, productos, cliente_id=None):
    response = client.post(
        "/api/v1/ventas",
        json={"cliente_id": cliente_id, "productos": productos},
    )
    assert response.status_code == 201
    return response.json()


def test_venta_un_producto_sin_cliente_descuenta_stock_y_movimiento(client):
    producto = crear_producto(
        client,
        sku="SALE-UNO",
        nombre="Invictus",
        stock_actual=10,
        precio="280.00",
    )

    venta = crear_venta(
        client,
        [{"producto_id": producto["id"], "cantidad": 2}],
    )

    assert venta["cliente_id"] is None
    assert venta["cliente_nombre"] == "Cliente mostrador"
    assert venta["estado"] == "COMPLETADA"
    assert venta["subtotal"] == "560.00"
    assert venta["total"] == "560.00"
    assert len(venta["detalles"]) == 1
    detalle = venta["detalles"][0]
    assert detalle["producto_id"] == producto["id"]
    assert detalle["producto_sku"] == "SALE-UNO"
    assert detalle["producto_nombre"] == "Invictus"
    assert detalle["precio_unitario"] == "280.00"
    assert detalle["cantidad"] == 2
    assert detalle["subtotal"] == "560.00"
    assert obtener_producto(client, producto["id"])["stock_actual"] == 8

    response = client.get(
        "/api/v1/inventario/movimientos",
        params={"producto_id": producto["id"], "tipo": "SALIDA"},
    )
    assert response.status_code == 200
    movimiento = response.json()["items"][0]
    assert movimiento["cantidad"] == 2
    assert movimiento["stock_anterior"] == 10
    assert movimiento["stock_nuevo"] == 8
    assert movimiento["motivo"] == f"Venta #{venta['id']}"


def test_venta_varios_productos_agrupa_repetidos_y_cliente_registrado(client):
    cliente = crear_cliente(client, "Maria Perez")
    producto_a = crear_producto(
        client,
        sku="SALE-A",
        nombre="Perfume A",
        stock_actual=10,
        precio="100.00",
    )
    producto_b = crear_producto(
        client,
        sku="SALE-B",
        nombre="Perfume B",
        stock_actual=5,
        precio="300.00",
    )

    venta = crear_venta(
        client,
        [
            {"producto_id": producto_a["id"], "cantidad": 2},
            {"producto_id": producto_b["id"], "cantidad": 1},
            {"producto_id": producto_a["id"], "cantidad": 3},
        ],
        cliente_id=cliente["id"],
    )

    assert venta["cliente_id"] == cliente["id"]
    assert venta["cliente_nombre"] == "Maria Perez"
    assert venta["subtotal"] == "800.00"
    assert venta["total"] == "800.00"
    assert len(venta["detalles"]) == 2
    detalles = {detalle["producto_id"]: detalle for detalle in venta["detalles"]}
    assert detalles[producto_a["id"]]["cantidad"] == 5
    assert detalles[producto_a["id"]]["subtotal"] == "500.00"
    assert detalles[producto_b["id"]]["cantidad"] == 1
    assert detalles[producto_b["id"]]["subtotal"] == "300.00"
    assert obtener_producto(client, producto_a["id"])["stock_actual"] == 5
    assert obtener_producto(client, producto_b["id"])["stock_actual"] == 4


def test_cliente_inexistente_e_inactivo(client):
    producto = crear_producto(client, sku="SALE-CLIENTE")

    response = client.post(
        "/api/v1/ventas",
        json={
            "cliente_id": 999,
            "productos": [{"producto_id": producto["id"], "cantidad": 1}],
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Cliente no encontrado."

    cliente = crear_cliente(client, "Cliente Inactivo")
    assert client.delete(f"/api/v1/clientes/{cliente['id']}").status_code == 200

    response = client.post(
        "/api/v1/ventas",
        json={
            "cliente_id": cliente["id"],
            "productos": [{"producto_id": producto["id"], "cantidad": 1}],
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "El cliente esta inactivo."


def test_producto_inexistente_inactivo_y_cantidades_invalidas(client):
    response = client.post(
        "/api/v1/ventas",
        json={"productos": [{"producto_id": 999, "cantidad": 1}]},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Producto no encontrado."

    producto = crear_producto(client, sku="SALE-INACTIVO")
    assert client.delete(f"/api/v1/productos/{producto['id']}").status_code == 200

    response = client.post(
        "/api/v1/ventas",
        json={"productos": [{"producto_id": producto["id"], "cantidad": 1}]},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "El producto esta inactivo."

    producto_activo = crear_producto(client, sku="SALE-CANTIDAD")
    for cantidad in (0, -1):
        response = client.post(
            "/api/v1/ventas",
            json={"productos": [{"producto_id": producto_activo["id"], "cantidad": cantidad}]},
        )
        assert response.status_code == 422

    response = client.post("/api/v1/ventas", json={"productos": []})
    assert response.status_code == 422


def test_stock_insuficiente_hace_rollback_completo(client):
    producto_a = crear_producto(
        client,
        sku="SALE-ROLL-A",
        nombre="Perfume A",
        stock_actual=10,
    )
    producto_b = crear_producto(
        client,
        sku="SALE-ROLL-B",
        nombre="Perfume B",
        stock_actual=1,
    )

    response = client.post(
        "/api/v1/ventas",
        json={
            "productos": [
                {"producto_id": producto_a["id"], "cantidad": 2},
                {"producto_id": producto_b["id"], "cantidad": 3},
            ]
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "No hay suficiente stock para el producto Perfume B."
    )
    assert client.get("/api/v1/ventas").json()["total"] == 0
    assert obtener_producto(client, producto_a["id"])["stock_actual"] == 10
    assert obtener_producto(client, producto_b["id"])["stock_actual"] == 1
    assert client.get("/api/v1/inventario/movimientos").json()["total"] == 0


def test_precio_sale_de_db_y_schema_rechaza_campos_extra(client):
    producto = crear_producto(
        client,
        sku="SALE-PRECIO",
        nombre="Producto Precio",
        stock_actual=10,
        precio="280.00",
    )

    response = client.post(
        "/api/v1/ventas",
        json={
            "productos": [
                {"producto_id": producto["id"], "cantidad": 2, "precio": "1.00"}
            ]
        },
    )
    assert response.status_code == 422

    response = client.post(
        "/api/v1/ventas",
        json={
            "estado": "ANULADA",
            "productos": [{"producto_id": producto["id"], "cantidad": 2}],
        },
    )
    assert response.status_code == 422

    venta = crear_venta(
        client,
        [{"producto_id": producto["id"], "cantidad": 2}],
    )
    detalle = venta["detalles"][0]
    assert detalle["precio_unitario"] == "280.00"
    assert detalle["subtotal"] == "560.00"
    assert venta["total"] == "560.00"


def test_listar_obtener_filtros_paginacion_y_venta_inexistente(client):
    cliente = crear_cliente(client, "Cliente Filtro")
    producto_a = crear_producto(client, sku="SALE-LIST-A", precio="100.00")
    producto_b = crear_producto(client, sku="SALE-LIST-B", precio="200.00")
    desde = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

    venta_a = crear_venta(
        client,
        [{"producto_id": producto_a["id"], "cantidad": 1}],
        cliente_id=cliente["id"],
    )
    venta_b = crear_venta(client, [{"producto_id": producto_b["id"], "cantidad": 1}])
    hasta = (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()

    response = client.post(
        f"/api/v1/ventas/{venta_b['id']}/anular",
        json={"motivo": "Filtro"},
    )
    assert response.status_code == 200

    response = client.get("/api/v1/ventas")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["items"][0]["id"] == venta_b["id"]

    response = client.get("/api/v1/ventas", params={"cliente_id": cliente["id"]})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == venta_a["id"]

    response = client.get("/api/v1/ventas", params={"estado": "COMPLETADA"})
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = client.get("/api/v1/ventas", params={"estado": "ANULADA"})
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = client.get("/api/v1/ventas", params={"desde": desde, "hasta": hasta})
    assert response.status_code == 200
    assert response.json()["total"] == 2

    response = client.get("/api/v1/ventas", params={"hasta": desde})
    assert response.status_code == 200
    assert response.json()["total"] == 0

    response = client.get("/api/v1/ventas", params={"page": 2, "limit": 1})
    assert response.status_code == 200
    assert response.json()["page"] == 2
    assert response.json()["limit"] == 1
    assert response.json()["total"] == 2
    assert response.json()["pages"] == 2

    response = client.get(f"/api/v1/ventas/{venta_a['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == venta_a["id"]

    response = client.get("/api/v1/ventas/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Venta no encontrada."


def test_anulacion_repone_stock_movimientos_entrada_y_doble_anulacion(client):
    producto_a = crear_producto(client, sku="SALE-ANUL-A", stock_actual=10)
    producto_b = crear_producto(client, sku="SALE-ANUL-B", stock_actual=5)
    venta = crear_venta(
        client,
        [
            {"producto_id": producto_a["id"], "cantidad": 2},
            {"producto_id": producto_b["id"], "cantidad": 1},
        ],
    )
    assert obtener_producto(client, producto_a["id"])["stock_actual"] == 8
    assert obtener_producto(client, producto_b["id"])["stock_actual"] == 4

    response = client.post(
        f"/api/v1/ventas/{venta['id']}/anular",
        json={"motivo": "Cliente cancelo"},
    )

    assert response.status_code == 200
    anulada = response.json()
    assert anulada["estado"] == "ANULADA"
    assert anulada["anulada_at"] is not None
    assert anulada["motivo_anulacion"] == "Cliente cancelo"
    assert obtener_producto(client, producto_a["id"])["stock_actual"] == 10
    assert obtener_producto(client, producto_b["id"])["stock_actual"] == 5

    response = client.get("/api/v1/inventario/movimientos", params={"tipo": "ENTRADA"})
    assert response.status_code == 200
    movimientos = response.json()["items"]
    assert len(movimientos) == 2
    assert all(
        movimiento["motivo"] == f"Anulacion de venta #{venta['id']}: Cliente cancelo"
        for movimiento in movimientos
    )

    response = client.post(
        f"/api/v1/ventas/{venta['id']}/anular",
        json={"motivo": "Otro intento"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "La venta ya esta anulada."
    assert obtener_producto(client, producto_a["id"])["stock_actual"] == 10
    assert obtener_producto(client, producto_b["id"])["stock_actual"] == 5

    venta_nueva = crear_venta(
        client,
        [{"producto_id": producto_a["id"], "cantidad": 1}],
    )
    response = client.post(
        f"/api/v1/ventas/{venta_nueva['id']}/anular",
        json={"motivo": "   "},
    )
    assert response.status_code == 422


def test_snapshot_historico_de_producto(client):
    producto = crear_producto(
        client,
        sku="SALE-SNAP",
        nombre="Invictus",
        stock_actual=10,
        precio="280.00",
    )
    venta = crear_venta(client, [{"producto_id": producto["id"], "cantidad": 2}])

    response = client.patch(
        f"/api/v1/productos/{producto['id']}",
        json={"nombre": "Invictus Nuevo", "precio": "300.00"},
    )
    assert response.status_code == 200

    response = client.get(f"/api/v1/ventas/{venta['id']}")
    assert response.status_code == 200
    detalle = response.json()["detalles"][0]
    assert detalle["producto_nombre"] == "Invictus"
    assert detalle["producto_sku"] == "SALE-SNAP"
    assert detalle["precio_unitario"] == "280.00"
    assert detalle["subtotal"] == "560.00"
