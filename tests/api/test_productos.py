def crear_categoria(client, nombre="Hombre"):
    response = client.post("/api/v1/categorias", json={"nombre": nombre})
    assert response.status_code == 201
    return response.json()


def producto_payload(categoria_id, **overrides):
    data = {
        "sku": "PERF-001",
        "nombre": "Invictus",
        "marca": "Rabanne",
        "descripcion": "Fragancia masculina",
        "categoria_id": categoria_id,
        "costo": "150.00",
        "precio": "280.00",
        "stock_actual": 20,
        "stock_minimo": 5,
        "ml": 50,
        "genero": "Hombre",
        "anio_lanzamiento": 2013,
    }
    data.update(overrides)
    return data


def test_crear_listar_obtener_actualizar_patch_y_soft_delete_producto(client):
    categoria = crear_categoria(client)
    response = client.post(
        "/api/v1/productos",
        json=producto_payload(categoria["id"]),
    )

    assert response.status_code == 201
    producto = response.json()
    assert producto["sku"] == "PERF-001"
    assert producto["costo"] == "150.00"
    assert producto["precio"] == "280.00"

    response = client.get("/api/v1/productos")
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = client.get(f"/api/v1/productos/{producto['id']}")
    assert response.status_code == 200
    assert response.json()["nombre"] == "Invictus"

    response = client.put(
        f"/api/v1/productos/{producto['id']}",
        json=producto_payload(
            categoria["id"],
            sku="PERF-002",
            nombre="Invictus Legend",
            precio="300.00",
        ),
    )
    assert response.status_code == 200
    assert response.json()["sku"] == "PERF-002"
    assert response.json()["precio"] == "300.00"

    response = client.patch(
        f"/api/v1/productos/{producto['id']}",
        json={"stock_actual": 2, "stock_minimo": 5},
    )
    assert response.status_code == 200
    assert response.json()["stock_actual"] == 2

    response = client.delete(f"/api/v1/productos/{producto['id']}")
    assert response.status_code == 200
    assert response.json()["activo"] is False

    response = client.get("/api/v1/productos")
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_producto_inexistente(client):
    response = client.get("/api/v1/productos/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Producto no encontrado."


def test_sku_duplicado(client):
    categoria = crear_categoria(client)
    response = client.post(
        "/api/v1/productos",
        json=producto_payload(categoria["id"], sku="PERF-001"),
    )
    assert response.status_code == 201

    response = client.post(
        "/api/v1/productos",
        json=producto_payload(categoria["id"], sku="perf-001", nombre="Otro"),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Ya existe un producto con ese SKU."


def test_categoria_inexistente_para_producto(client):
    response = client.post("/api/v1/productos", json=producto_payload(999))

    assert response.status_code == 404
    assert response.json()["detail"] == "La categoria indicada no existe."


def test_categoria_inactiva_para_producto(client):
    categoria = crear_categoria(client)
    response = client.delete(f"/api/v1/categorias/{categoria['id']}")
    assert response.status_code == 200

    response = client.post(
        "/api/v1/productos",
        json=producto_payload(categoria["id"]),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "No se puede asociar el producto a una categoria inactiva."
    )


def test_validaciones_producto(client):
    categoria = crear_categoria(client)
    casos = [
        {"precio": "-1"},
        {"costo": "-1"},
        {"stock_actual": -1},
        {"stock_minimo": -1},
        {"ml": 0},
        {"sku": ""},
        {"nombre": ""},
        {"marca": ""},
    ]

    for overrides in casos:
        response = client.post(
            "/api/v1/productos",
            json=producto_payload(categoria["id"], **overrides),
        )
        assert response.status_code == 422


def test_filtros_busqueda_stock_bajo_y_paginacion(client):
    hombre = crear_categoria(client, "Hombre")
    mujer = crear_categoria(client, "Mujer")
    productos = [
        producto_payload(
            hombre["id"],
            sku="PERF-001",
            nombre="Invictus",
            marca="Rabanne",
            stock_actual=2,
            stock_minimo=5,
            genero="Hombre",
        ),
        producto_payload(
            mujer["id"],
            sku="PERF-002",
            nombre="Good Girl",
            marca="Carolina Herrera",
            stock_actual=9,
            stock_minimo=3,
            genero="Mujer",
        ),
        producto_payload(
            hombre["id"],
            sku="PERF-003",
            nombre="Phantom",
            marca="Rabanne",
            stock_actual=8,
            stock_minimo=4,
            genero="Hombre",
        ),
    ]
    for producto in productos:
        assert client.post("/api/v1/productos", json=producto).status_code == 201

    response = client.get("/api/v1/productos", params={"buscar": "victus"})
    assert response.status_code == 200
    assert response.json()["items"][0]["nombre"] == "Invictus"

    response = client.get("/api/v1/productos", params={"marca": "Rabanne"})
    assert response.status_code == 200
    assert response.json()["total"] == 2

    response = client.get(
        "/api/v1/productos",
        params={"categoria_id": mujer["id"]},
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["nombre"] == "Good Girl"

    response = client.get("/api/v1/productos", params={"stock_bajo": "true"})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["nombre"] == "Invictus"

    response = client.get("/api/v1/productos", params={"page": 2, "limit": 2})
    assert response.status_code == 200
    assert response.json()["page"] == 2
    assert response.json()["limit"] == 2
    assert response.json()["total"] == 3
    assert response.json()["pages"] == 2
