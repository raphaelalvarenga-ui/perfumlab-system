from sqlalchemy import select

from app.models.orm.factura import FacturaORM
from app.models.orm.movimiento_inventario import MovimientoInventarioORM
from app.models.orm.venta import VentaORM
from app.models.tipos import TipoMovimientoInventario


def login(client, username, password):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def crear_categoria(client, nombre="Permisos"):
    response = client.post("/api/v1/categorias", json={"nombre": nombre})
    assert response.status_code == 201
    return response.json()


def producto_payload(categoria_id, **overrides):
    data = {
        "sku": "PERM-001",
        "nombre": "Producto Permisos",
        "marca": "Marca Permisos",
        "descripcion": "Producto temporal de permisos",
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


def crear_producto(client, categoria_id, **overrides):
    response = client.post(
        "/api/v1/productos",
        json=producto_payload(categoria_id, **overrides),
    )
    assert response.status_code == 201
    return response.json()


def test_matriz_permisos_sin_token_vendedor_y_admin(
    client,
    public_client,
    vendedor_headers,
):
    response = public_client.get("/api/v1/productos")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"

    assert client.get("/api/v1/productos", headers=vendedor_headers).status_code == 200

    response = client.post(
        "/api/v1/productos",
        headers=vendedor_headers,
        json=producto_payload(1, sku="PERM-DENY-PROD"),
    )
    assert response.status_code == 403

    response = client.post(
        "/api/v1/inventario/ajuste",
        headers=vendedor_headers,
        json={"producto_id": 1, "stock_nuevo": 1, "motivo": "No permitido"},
    )
    assert response.status_code == 403

    response = client.get("/api/v1/reportes/resumen", headers=vendedor_headers)
    assert response.status_code == 403

    categoria = crear_categoria(client, "Permisos Admin")
    producto = crear_producto(client, categoria["id"], sku="PERM-ADMIN")

    response = client.post(
        "/api/v1/inventario/ajuste",
        json={
            "producto_id": producto["id"],
            "stock_nuevo": 15,
            "motivo": "Ajuste admin",
        },
    )
    assert response.status_code == 201

    response = client.get("/api/v1/reportes/resumen")
    assert response.status_code == 200

    response = client.post(
        "/api/v1/ventas",
        json={"productos": [{"producto_id": producto["id"], "cantidad": 1}]},
    )
    assert response.status_code == 201
    venta = response.json()

    response = client.post(f"/api/v1/ventas/{venta['id']}/factura")
    assert response.status_code == 201

    response = client.post(
        f"/api/v1/ventas/{venta['id']}/anular",
        json={"motivo": "Admin anula"},
    )
    assert response.status_code == 200


def test_vendedor_crea_cliente_venta_factura_y_admin_anula_con_auditoria(
    client,
    vendedor_headers,
    vendedor_user,
    admin_user,
    db_session,
):
    categoria = crear_categoria(client, "Auditoria")
    producto = crear_producto(client, categoria["id"], sku="AUD-VENTA", precio="100.00")

    response = client.post(
        "/api/v1/clientes",
        headers=vendedor_headers,
        json={"nombre": "Cliente Auditoria"},
    )
    assert response.status_code == 201
    cliente = response.json()

    response = client.post(
        "/api/v1/ventas",
        headers=vendedor_headers,
        json={
            "cliente_id": cliente["id"],
            "productos": [{"producto_id": producto["id"], "cantidad": 2}],
        },
    )
    assert response.status_code == 201
    venta = response.json()
    assert venta["usuario_id"] == vendedor_user["id"]
    assert venta["anulada_por_usuario_id"] is None

    movimiento_salida = db_session.execute(
        select(MovimientoInventarioORM).where(
            MovimientoInventarioORM.producto_id == producto["id"],
            MovimientoInventarioORM.tipo == TipoMovimientoInventario.SALIDA,
        )
    ).scalar_one()
    assert movimiento_salida.usuario_id == vendedor_user["id"]

    response = client.post(
        f"/api/v1/ventas/{venta['id']}/factura",
        headers=vendedor_headers,
    )
    assert response.status_code == 201
    factura = response.json()
    assert factura["usuario_id"] == vendedor_user["id"]
    assert factura["anulada_por_usuario_id"] is None

    response = client.post(
        f"/api/v1/ventas/{venta['id']}/anular",
        json={"motivo": "Auditoria admin"},
    )
    assert response.status_code == 200
    venta_anulada = response.json()
    assert venta_anulada["usuario_id"] == vendedor_user["id"]
    assert venta_anulada["anulada_por_usuario_id"] == admin_user["id"]

    venta_db = db_session.get(VentaORM, venta["id"])
    factura_db = db_session.get(FacturaORM, factura["id"])
    assert venta_db.usuario_id == vendedor_user["id"]
    assert venta_db.anulada_por_usuario_id == admin_user["id"]
    assert factura_db.usuario_id == vendedor_user["id"]
    assert factura_db.anulada_por_usuario_id == admin_user["id"]

    movimiento_entrada = db_session.execute(
        select(MovimientoInventarioORM).where(
            MovimientoInventarioORM.producto_id == producto["id"],
            MovimientoInventarioORM.tipo == TipoMovimientoInventario.ENTRADA,
        )
    ).scalar_one()
    assert movimiento_entrada.usuario_id == admin_user["id"]


def test_usuario_desactivado_con_token_existente_falla(
    client,
    public_client,
    vendedor_user,
):
    token = login(public_client, vendedor_user["username"], vendedor_user["password"])

    response = client.delete(f"/api/v1/usuarios/{vendedor_user['id']}")
    assert response.status_code == 200

    response = public_client.get("/api/v1/productos", headers=bearer(token))
    assert response.status_code == 401


def test_cambio_rol_en_caliente_usa_rol_actual_desde_db(
    client,
    public_client,
    vendedor_user,
):
    token = login(public_client, vendedor_user["username"], vendedor_user["password"])
    headers = bearer(token)

    response = public_client.post(
        "/api/v1/categorias",
        headers=headers,
        json={"nombre": "Rol Caliente Admin"},
    )
    assert response.status_code == 403

    response = client.patch(
        f"/api/v1/usuarios/{vendedor_user['id']}",
        json={"rol": "ADMINISTRADOR"},
    )
    assert response.status_code == 200

    response = public_client.post(
        "/api/v1/categorias",
        headers=headers,
        json={"nombre": "Rol Caliente Admin"},
    )
    assert response.status_code == 201

    response = client.patch(
        f"/api/v1/usuarios/{vendedor_user['id']}",
        json={"rol": "VENDEDOR"},
    )
    assert response.status_code == 200

    response = public_client.post(
        "/api/v1/categorias",
        headers=headers,
        json={"nombre": "Rol Caliente Denegado"},
    )
    assert response.status_code == 403
