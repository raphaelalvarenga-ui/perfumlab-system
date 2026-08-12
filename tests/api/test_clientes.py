def cliente_payload(**overrides):
    data = {
        "nombre": "Juan Perez",
        "correo": "Juan@Example.com",
        "telefono": "9999-9999",
        "direccion": "La Paz",
    }
    data.update(overrides)
    return data


def test_crear_cliente_completo_normaliza_datos(client):
    response = client.post(
        "/api/v1/clientes",
        json=cliente_payload(nombre="  Juan   Perez  "),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Juan Perez"
    assert data["correo"] == "juan@example.com"
    assert data["telefono"] == "9999-9999"
    assert data["direccion"] == "La Paz"
    assert data["activo"] is True


def test_crear_cliente_solo_con_nombre(client):
    response = client.post(
        "/api/v1/clientes",
        json={
            "nombre": "Cliente mostrador",
            "correo": None,
            "telefono": None,
            "direccion": None,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Cliente mostrador"
    assert data["correo"] is None
    assert data["telefono"] is None
    assert data["direccion"] is None


def test_crear_multiples_clientes_sin_correo(client):
    for nombre in ("Cliente Uno", "Cliente Dos", "Cliente Tres"):
        response = client.post(
            "/api/v1/clientes",
            json={"nombre": nombre, "correo": ""},
        )
        assert response.status_code == 201
        assert response.json()["correo"] is None


def test_listar_obtener_buscar_filtrar_y_paginar_clientes(client):
    clientes = [
        cliente_payload(nombre="Ana Lopez", correo="ana@example.com", telefono="9999-0001"),
        cliente_payload(nombre="Beto Ruiz", correo="beto@example.com", telefono="9999-0002"),
        cliente_payload(nombre="Carla Soto", correo=None, telefono="8888-0003"),
    ]
    ids = []
    for payload in clientes:
        response = client.post("/api/v1/clientes", json=payload)
        assert response.status_code == 201
        ids.append(response.json()["id"])

    response = client.get("/api/v1/clientes")
    assert response.status_code == 200
    assert response.json()["total"] == 3

    response = client.get(f"/api/v1/clientes/{ids[0]}")
    assert response.status_code == 200
    assert response.json()["nombre"] == "Ana Lopez"

    assert client.get("/api/v1/clientes", params={"buscar": "Ana"}).json()["total"] == 1
    assert client.get("/api/v1/clientes", params={"buscar": "beto@example"}).json()["total"] == 1
    assert client.get("/api/v1/clientes", params={"buscar": "8888"}).json()["total"] == 1

    response = client.delete(f"/api/v1/clientes/{ids[1]}")
    assert response.status_code == 200
    assert response.json()["activo"] is False

    response = client.get("/api/v1/clientes", params={"activo": "false"})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["nombre"] == "Beto Ruiz"

    response = client.get("/api/v1/clientes", params={"page": 2, "limit": 2})
    assert response.status_code == 200
    assert response.json()["page"] == 2
    assert response.json()["limit"] == 2
    assert response.json()["total"] == 2
    assert response.json()["pages"] == 1


def test_put_patch_y_soft_delete_cliente(client):
    cliente = client.post("/api/v1/clientes", json=cliente_payload()).json()

    response = client.put(
        f"/api/v1/clientes/{cliente['id']}",
        json={
            "nombre": "Juan Editado",
            "correo": None,
            "telefono": None,
            "direccion": None,
            "activo": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["nombre"] == "Juan Editado"
    assert response.json()["correo"] is None

    response = client.patch(
        f"/api/v1/clientes/{cliente['id']}",
        json={"correo": "nuevo@example.com", "telefono": "2222-3333"},
    )
    assert response.status_code == 200
    assert response.json()["correo"] == "nuevo@example.com"
    assert response.json()["telefono"] == "2222-3333"

    response = client.delete(f"/api/v1/clientes/{cliente['id']}")
    assert response.status_code == 200
    assert response.json()["activo"] is False

    response = client.get("/api/v1/clientes")
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_cliente_inexistente(client):
    response = client.get("/api/v1/clientes/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Cliente no encontrado."


def test_correo_invalido_y_duplicado(client):
    response = client.post(
        "/api/v1/clientes",
        json=cliente_payload(correo="cliente@"),
    )
    assert response.status_code == 422

    response = client.post(
        "/api/v1/clientes",
        json=cliente_payload(correo="cliente@example.com"),
    )
    assert response.status_code == 201

    response = client.post(
        "/api/v1/clientes",
        json=cliente_payload(nombre="Duplicado", correo="CLIENTE@EXAMPLE.COM"),
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Ya existe un cliente con ese correo."


def test_correo_duplicado_en_patch(client):
    primero = client.post(
        "/api/v1/clientes",
        json=cliente_payload(nombre="Primero", correo="primero@example.com"),
    ).json()
    segundo = client.post(
        "/api/v1/clientes",
        json=cliente_payload(nombre="Segundo", correo="segundo@example.com"),
    ).json()

    response = client.patch(
        f"/api/v1/clientes/{segundo['id']}",
        json={"correo": "PRIMERO@EXAMPLE.COM"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Ya existe un cliente con ese correo."

    response = client.get(f"/api/v1/clientes/{primero['id']}")
    assert response.status_code == 200


def test_campos_vacios(client):
    casos = [
        {"nombre": ""},
        {"nombre": "   "},
        {"nombre": "Cliente Valido", "telefono": "123"},
        {"nombre": "Cliente Valido", "direccion": "\u0000"},
    ]

    for payload in casos:
        response = client.post("/api/v1/clientes", json=payload)
        assert response.status_code == 422
