import pytest

from app.models.tipos import EstadoFactura
from app.repositories.facturas_repository import FacturasRepository


def crear_categoria(client, nombre="Facturas"):
    response = client.post("/api/v1/categorias", json={"nombre": nombre})
    assert response.status_code == 201
    return response.json()


def producto_payload(categoria_id, **overrides):
    data = {
        "sku": "FAC-TEST-001",
        "nombre": "Producto Factura",
        "marca": "Marca Factura",
        "descripcion": "Producto temporal de factura",
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
    sku="FAC-TEST-001",
    nombre="Producto Factura",
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


def crear_cliente(client, nombre="Cliente Factura"):
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


def obtener_producto(client, producto_id):
    response = client.get(f"/api/v1/productos/{producto_id}")
    assert response.status_code == 200
    return response.json()


def test_generar_factura_con_cliente_numero_total_y_snapshots(client):
    cliente = crear_cliente(client, "Juan Perez")
    producto = crear_producto(
        client,
        sku="FAC-UNO",
        nombre="Invictus",
        stock_actual=10,
        precio="280.00",
    )
    venta = crear_venta(
        client,
        [{"producto_id": producto["id"], "cantidad": 3}],
        cliente_id=cliente["id"],
    )

    factura = generar_factura(client, venta["id"])

    assert factura["numero"] == f"FAC-{venta['id']:06d}"
    assert factura["venta_id"] == venta["id"]
    assert factura["cliente_nombre"] == "Juan Perez"
    assert factura["subtotal"] == "840.00"
    assert factura["total"] == "840.00"
    assert factura["estado"] == "EMITIDA"
    assert factura["anulada_at"] is None
    assert factura["motivo_anulacion"] is None
    assert len(factura["detalles"]) == 1
    detalle = factura["detalles"][0]
    assert detalle["producto_id"] == producto["id"]
    assert detalle["producto_sku"] == "FAC-UNO"
    assert detalle["producto_nombre"] == "Invictus"
    assert detalle["precio_unitario"] == "280.00"
    assert detalle["cantidad"] == 3
    assert detalle["subtotal"] == "840.00"


def test_factura_cliente_mostrador(client):
    producto = crear_producto(client, sku="FAC-MOSTRADOR")
    venta = crear_venta(client, [{"producto_id": producto["id"], "cantidad": 1}])

    factura = generar_factura(client, venta["id"])

    assert factura["cliente_nombre"] == "Cliente mostrador"
    assert factura["total"] == "280.00"


def test_obtener_por_id_numero_listar_buscar_filtrar_y_paginar(client):
    cliente = crear_cliente(client, "Cliente Busqueda")
    producto_a = crear_producto(client, sku="FAC-LIST-A", precio="100.00")
    producto_b = crear_producto(client, sku="FAC-LIST-B", precio="200.00")
    venta_a = crear_venta(
        client,
        [{"producto_id": producto_a["id"], "cantidad": 1}],
        cliente_id=cliente["id"],
    )
    venta_b = crear_venta(client, [{"producto_id": producto_b["id"], "cantidad": 1}])
    factura_a = generar_factura(client, venta_a["id"])
    factura_b = generar_factura(client, venta_b["id"])

    response = client.post(
        f"/api/v1/ventas/{venta_b['id']}/anular",
        json={"motivo": "Filtro facturas"},
    )
    assert response.status_code == 200

    response = client.get(f"/api/v1/facturas/{factura_a['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == factura_a["id"]

    response = client.get(f"/api/v1/facturas/numero/{factura_a['numero']}")
    assert response.status_code == 200
    assert response.json()["numero"] == factura_a["numero"]

    response = client.get("/api/v1/facturas")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["items"][0]["id"] == factura_b["id"]

    response = client.get("/api/v1/facturas", params={"venta_id": venta_a["id"]})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == factura_a["id"]

    response = client.get("/api/v1/facturas", params={"estado": "EMITIDA"})
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = client.get("/api/v1/facturas", params={"estado": "ANULADA"})
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = client.get("/api/v1/facturas", params={"buscar": "Busqueda"})
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = client.get("/api/v1/facturas", params={"buscar": factura_b["numero"]})
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = client.get("/api/v1/facturas", params={"page": 2, "limit": 1})
    assert response.status_code == 200
    assert response.json()["page"] == 2
    assert response.json()["limit"] == 1
    assert response.json()["total"] == 2
    assert response.json()["pages"] == 2


def test_venta_inexistente_anulada_doble_factura_e_inexistente(client):
    response = client.post("/api/v1/ventas/999/factura")
    assert response.status_code == 404
    assert response.json()["detail"] == "Venta no encontrada."

    producto = crear_producto(client, sku="FAC-VALIDA")
    venta = crear_venta(client, [{"producto_id": producto["id"], "cantidad": 1}])
    response = client.post(
        f"/api/v1/ventas/{venta['id']}/anular",
        json={"motivo": "No facturable"},
    )
    assert response.status_code == 200

    response = client.post(f"/api/v1/ventas/{venta['id']}/factura")
    assert response.status_code == 409
    assert response.json()["detail"] == "No se puede facturar una venta anulada."

    venta_facturable = crear_venta(client, [{"producto_id": producto["id"], "cantidad": 1}])
    factura = generar_factura(client, venta_facturable["id"])
    response = client.post(f"/api/v1/ventas/{venta_facturable['id']}/factura")
    assert response.status_code == 409
    assert response.json()["detail"] == "La venta ya tiene una factura."

    response = client.get("/api/v1/facturas/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Factura no encontrada."

    response = client.get("/api/v1/facturas/numero/FAC-999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Factura no encontrada."

    assert factura["estado"] == "EMITIDA"


def test_factura_no_permite_edicion_ni_borrado(client):
    producto = crear_producto(client, sku="FAC-NO-EDIT")
    venta = crear_venta(client, [{"producto_id": producto["id"], "cantidad": 1}])
    factura = generar_factura(client, venta["id"])

    for method in (client.put, client.patch, client.delete):
        response = method(f"/api/v1/facturas/{factura['id']}")
        assert response.status_code == 405


def test_factura_sigue_mostrando_precio_y_nombre_historicos(client):
    producto = crear_producto(
        client,
        sku="FAC-SNAP",
        nombre="Invictus",
        stock_actual=10,
        precio="280.00",
    )
    venta = crear_venta(client, [{"producto_id": producto["id"], "cantidad": 2}])
    factura = generar_factura(client, venta["id"])

    response = client.patch(
        f"/api/v1/productos/{producto['id']}",
        json={"nombre": "Invictus Nuevo", "precio": "350.00"},
    )
    assert response.status_code == 200

    response = client.get(f"/api/v1/facturas/{factura['id']}")
    assert response.status_code == 200
    detalle = response.json()["detalles"][0]
    assert detalle["producto_nombre"] == "Invictus"
    assert detalle["producto_sku"] == "FAC-SNAP"
    assert detalle["precio_unitario"] == "280.00"
    assert detalle["subtotal"] == "560.00"


def test_anular_venta_facturada_anula_factura_y_repone_stock(client):
    producto = crear_producto(client, sku="FAC-ANULA", stock_actual=10)
    venta = crear_venta(client, [{"producto_id": producto["id"], "cantidad": 2}])
    factura = generar_factura(client, venta["id"])
    assert obtener_producto(client, producto["id"])["stock_actual"] == 8

    response = client.post(
        f"/api/v1/ventas/{venta['id']}/anular",
        json={"motivo": "Cliente cancelo"},
    )
    assert response.status_code == 200
    assert response.json()["estado"] == "ANULADA"
    assert obtener_producto(client, producto["id"])["stock_actual"] == 10

    response = client.get(f"/api/v1/facturas/{factura['id']}")
    assert response.status_code == 200
    factura_anulada = response.json()
    assert factura_anulada["estado"] == "ANULADA"
    assert factura_anulada["numero"] == factura["numero"]
    assert factura_anulada["motivo_anulacion"] == "Cliente cancelo"
    assert factura_anulada["anulada_at"] is not None
    assert factura_anulada["detalles"][0]["producto_id"] == producto["id"]

    response = client.get(
        "/api/v1/inventario/movimientos",
        params={"producto_id": producto["id"], "tipo": "ENTRADA"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["cantidad"] == 2


def test_atomicidad_generar_factura_no_deja_factura_parcial(client, monkeypatch):
    producto = crear_producto(client, sku="FAC-ATOM-GEN")
    venta = crear_venta(client, [{"producto_id": producto["id"], "cantidad": 1}])
    original_create = FacturasRepository.create

    def fallar_create(self, datos):
        original_create(self, datos)
        raise RuntimeError("fallo controlado factura")

    monkeypatch.setattr(FacturasRepository, "create", fallar_create)

    with pytest.raises(RuntimeError, match="fallo controlado factura"):
        client.post(f"/api/v1/ventas/{venta['id']}/factura")

    response = client.get("/api/v1/facturas", params={"venta_id": venta["id"]})
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_atomicidad_anulacion_facturada_rollback_completo(client, monkeypatch):
    producto = crear_producto(client, sku="FAC-ATOM-ANULA", stock_actual=10)
    venta = crear_venta(client, [{"producto_id": producto["id"], "cantidad": 2}])
    factura = generar_factura(client, venta["id"])
    assert obtener_producto(client, producto["id"])["stock_actual"] == 8
    original_mark = FacturasRepository.mark_anulada

    def fallar_mark(
        self,
        factura_obj,
        *,
        motivo,
        anulada_at,
        anulada_por_usuario_id=None,
    ):
        original_mark(
            self,
            factura_obj,
            motivo=motivo,
            anulada_at=anulada_at,
            anulada_por_usuario_id=anulada_por_usuario_id,
        )
        raise RuntimeError("fallo controlado anulacion factura")

    monkeypatch.setattr(FacturasRepository, "mark_anulada", fallar_mark)

    with pytest.raises(RuntimeError, match="fallo controlado anulacion factura"):
        client.post(
            f"/api/v1/ventas/{venta['id']}/anular",
            json={"motivo": "Fallo controlado"},
        )

    response = client.get(f"/api/v1/ventas/{venta['id']}")
    assert response.status_code == 200
    assert response.json()["estado"] == "COMPLETADA"
    assert obtener_producto(client, producto["id"])["stock_actual"] == 8

    response = client.get(f"/api/v1/facturas/{factura['id']}")
    assert response.status_code == 200
    assert response.json()["estado"] == "EMITIDA"
    assert response.json()["motivo_anulacion"] is None

    response = client.get(
        "/api/v1/inventario/movimientos",
        params={"producto_id": producto["id"], "tipo": "ENTRADA"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0
