from datetime import datetime, timedelta, timezone

import pytest

from app.repositories.inventario_repository import InventarioRepository


def crear_categoria(client, nombre="Inventario"):
    response = client.post("/api/v1/categorias", json={"nombre": nombre})
    assert response.status_code == 201
    return response.json()


def producto_payload(categoria_id, **overrides):
    data = {
        "sku": "INV-001",
        "nombre": "Producto Inventario",
        "marca": "Marca QA",
        "descripcion": "Producto temporal de inventario",
        "categoria_id": categoria_id,
        "costo": "10.00",
        "precio": "20.00",
        "stock_actual": 10,
        "stock_minimo": 2,
        "ml": 50,
        "genero": "Unisex",
    }
    data.update(overrides)
    return data


def crear_producto(client, *, stock_actual=10, sku="INV-001", activo=True):
    categoria = crear_categoria(client, f"Inventario {sku}")
    response = client.post(
        "/api/v1/productos",
        json=producto_payload(
            categoria["id"],
            sku=sku,
            stock_actual=stock_actual,
            activo=activo,
        ),
    )
    assert response.status_code == 201
    return response.json()


def obtener_producto(client, producto_id):
    response = client.get(f"/api/v1/productos/{producto_id}")
    assert response.status_code == 200
    return response.json()


def test_entrada_correcta_incrementa_stock_y_registra_movimiento(client):
    producto = crear_producto(client, stock_actual=10)

    response = client.post(
        "/api/v1/inventario/entrada",
        json={
            "producto_id": producto["id"],
            "cantidad": 5,
            "motivo": " Compra de mercaderia ",
        },
    )

    assert response.status_code == 201
    movimiento = response.json()
    assert movimiento["producto_id"] == producto["id"]
    assert movimiento["tipo"] == "ENTRADA"
    assert movimiento["cantidad"] == 5
    assert movimiento["stock_anterior"] == 10
    assert movimiento["stock_nuevo"] == 15
    assert movimiento["motivo"] == "Compra de mercaderia"
    assert movimiento["usuario_id"] is None
    assert obtener_producto(client, producto["id"])["stock_actual"] == 15


def test_entrada_rechaza_producto_inexistente_inactivo_y_payload_invalido(client):
    response = client.post(
        "/api/v1/inventario/entrada",
        json={"producto_id": 999, "cantidad": 1, "motivo": "Entrada"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Producto no encontrado."

    producto = crear_producto(client, stock_actual=10, sku="INV-INACTIVO")
    assert client.delete(f"/api/v1/productos/{producto['id']}").status_code == 200

    response = client.post(
        "/api/v1/inventario/entrada",
        json={"producto_id": producto["id"], "cantidad": 1, "motivo": "Entrada"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "El producto esta inactivo."

    casos_invalidos = [
        {"producto_id": producto["id"], "cantidad": 0, "motivo": "Entrada"},
        {"producto_id": producto["id"], "cantidad": -1, "motivo": "Entrada"},
        {"producto_id": producto["id"], "cantidad": 1, "motivo": "   "},
    ]
    for payload in casos_invalidos:
        response = client.post("/api/v1/inventario/entrada", json=payload)
        assert response.status_code == 422


def test_salida_correcta_disminuye_stock_y_permite_llegar_a_cero(client):
    producto = crear_producto(client, stock_actual=10)

    response = client.post(
        "/api/v1/inventario/salida",
        json={"producto_id": producto["id"], "cantidad": 4, "motivo": "Venta"},
    )
    assert response.status_code == 201
    movimiento = response.json()
    assert movimiento["tipo"] == "SALIDA"
    assert movimiento["cantidad"] == 4
    assert movimiento["stock_anterior"] == 10
    assert movimiento["stock_nuevo"] == 6
    assert obtener_producto(client, producto["id"])["stock_actual"] == 6

    response = client.post(
        "/api/v1/inventario/salida",
        json={"producto_id": producto["id"], "cantidad": 6, "motivo": "Salida exacta"},
    )
    assert response.status_code == 201
    assert response.json()["stock_nuevo"] == 0
    assert obtener_producto(client, producto["id"])["stock_actual"] == 0


def test_salida_rechaza_stock_insuficiente_inexistente_inactivo_y_payload(client):
    producto = crear_producto(client, stock_actual=3)

    response = client.post(
        "/api/v1/inventario/salida",
        json={"producto_id": producto["id"], "cantidad": 4, "motivo": "Exceso"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "No hay suficiente stock disponible."
    assert obtener_producto(client, producto["id"])["stock_actual"] == 3

    response = client.get(
        "/api/v1/inventario/movimientos",
        params={"producto_id": producto["id"]},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0

    response = client.post(
        "/api/v1/inventario/salida",
        json={"producto_id": 999, "cantidad": 1, "motivo": "Salida"},
    )
    assert response.status_code == 404

    inactivo = crear_producto(client, stock_actual=5, sku="INV-SAL-INACTIVO")
    assert client.delete(f"/api/v1/productos/{inactivo['id']}").status_code == 200
    response = client.post(
        "/api/v1/inventario/salida",
        json={"producto_id": inactivo["id"], "cantidad": 1, "motivo": "Salida"},
    )
    assert response.status_code == 409

    for cantidad in (0, -1):
        response = client.post(
            "/api/v1/inventario/salida",
            json={"producto_id": producto["id"], "cantidad": cantidad, "motivo": "x"},
        )
        assert response.status_code == 422


def test_ajuste_sube_baja_y_llega_a_cero(client):
    producto = crear_producto(client, stock_actual=10)

    response = client.post(
        "/api/v1/inventario/ajuste",
        json={"producto_id": producto["id"], "stock_nuevo": 15, "motivo": "Conteo"},
    )
    assert response.status_code == 201
    assert response.json()["tipo"] == "AJUSTE"
    assert response.json()["cantidad"] == 5
    assert response.json()["stock_anterior"] == 10
    assert response.json()["stock_nuevo"] == 15

    response = client.post(
        "/api/v1/inventario/ajuste",
        json={"producto_id": producto["id"], "stock_nuevo": 7, "motivo": "Conteo"},
    )
    assert response.status_code == 201
    assert response.json()["cantidad"] == 8
    assert response.json()["stock_anterior"] == 15
    assert response.json()["stock_nuevo"] == 7

    response = client.post(
        "/api/v1/inventario/ajuste",
        json={"producto_id": producto["id"], "stock_nuevo": 0, "motivo": "Conteo"},
    )
    assert response.status_code == 201
    assert response.json()["stock_nuevo"] == 0
    assert obtener_producto(client, producto["id"])["stock_actual"] == 0


def test_ajuste_rechaza_stock_negativo_mismo_stock_inexistente_e_inactivo(client):
    producto = crear_producto(client, stock_actual=10)

    response = client.post(
        "/api/v1/inventario/ajuste",
        json={"producto_id": producto["id"], "stock_nuevo": -1, "motivo": "Conteo"},
    )
    assert response.status_code == 422

    response = client.post(
        "/api/v1/inventario/ajuste",
        json={"producto_id": producto["id"], "stock_nuevo": 10, "motivo": "Conteo"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "El ajuste no modifica el stock actual."

    response = client.post(
        "/api/v1/inventario/ajuste",
        json={"producto_id": 999, "stock_nuevo": 1, "motivo": "Conteo"},
    )
    assert response.status_code == 404

    inactivo = crear_producto(client, stock_actual=5, sku="INV-AJ-INACTIVO")
    assert client.delete(f"/api/v1/productos/{inactivo['id']}").status_code == 200
    response = client.post(
        "/api/v1/inventario/ajuste",
        json={"producto_id": inactivo["id"], "stock_nuevo": 1, "motivo": "Conteo"},
    )
    assert response.status_code == 409


def test_historial_filtra_pagina_ordena_y_obtiene_por_id(client):
    producto = crear_producto(client, stock_actual=10, sku="INV-HIST-1")
    otro_producto = crear_producto(client, stock_actual=5, sku="INV-HIST-2")
    desde = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

    movimientos = []
    for endpoint, payload in [
        (
            "entrada",
            {"producto_id": producto["id"], "cantidad": 2, "motivo": "Entrada"},
        ),
        (
            "salida",
            {"producto_id": producto["id"], "cantidad": 1, "motivo": "Salida"},
        ),
        (
            "ajuste",
            {"producto_id": producto["id"], "stock_nuevo": 8, "motivo": "Ajuste"},
        ),
        (
            "entrada",
            {
                "producto_id": otro_producto["id"],
                "cantidad": 3,
                "motivo": "Entrada otro",
            },
        ),
    ]:
        response = client.post(f"/api/v1/inventario/{endpoint}", json=payload)
        assert response.status_code == 201
        movimientos.append(response.json())

    hasta = (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()

    response = client.get("/api/v1/inventario/movimientos")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 4
    ids = [item["id"] for item in data["items"]]
    assert ids == sorted(ids, reverse=True)

    response = client.get(
        "/api/v1/inventario/movimientos",
        params={"producto_id": producto["id"]},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 3

    response = client.get(
        "/api/v1/inventario/movimientos",
        params={"tipo": "ENTRADA"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 2

    response = client.get(
        "/api/v1/inventario/movimientos",
        params={"desde": desde, "hasta": hasta},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 4

    response = client.get(
        "/api/v1/inventario/movimientos",
        params={"hasta": desde},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0

    response = client.get(
        "/api/v1/inventario/movimientos",
        params={"page": 2, "limit": 2},
    )
    assert response.status_code == 200
    assert response.json()["page"] == 2
    assert response.json()["limit"] == 2
    assert response.json()["total"] == 4
    assert response.json()["pages"] == 2

    movimiento_id = movimientos[0]["id"]
    response = client.get(f"/api/v1/inventario/movimientos/{movimiento_id}")
    assert response.status_code == 200
    assert response.json()["id"] == movimiento_id

    response = client.get("/api/v1/inventario/movimientos/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Movimiento de inventario no encontrado."


def test_atomicidad_rollback_si_falla_crear_movimiento(client, monkeypatch):
    producto = crear_producto(client, stock_actual=10)

    def fallar_create_movimiento(self, **kwargs):
        raise RuntimeError("fallo controlado")

    monkeypatch.setattr(
        InventarioRepository,
        "create_movimiento",
        fallar_create_movimiento,
    )

    with pytest.raises(RuntimeError, match="fallo controlado"):
        client.post(
            "/api/v1/inventario/entrada",
            json={
                "producto_id": producto["id"],
                "cantidad": 5,
                "motivo": "Fallo controlado",
            },
        )

    assert obtener_producto(client, producto["id"])["stock_actual"] == 10
    response = client.get(
        "/api/v1/inventario/movimientos",
        params={"producto_id": producto["id"]},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0
