def test_crear_listar_buscar_obtener_actualizar_y_soft_delete_acorde(client):
    response = client.post("/api/v1/acordes", json={"nombre": " C\u00edtrico "})
    assert response.status_code == 201
    acorde = response.json()
    assert acorde["nombre"] == "C\u00edtrico"
    assert acorde["slug"] == "citrico"
    assert acorde["activo"] is True

    response = client.get("/api/v1/acordes", params={"buscar": "citrico"})
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = client.get(f"/api/v1/acordes/{acorde['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == acorde["id"]

    response = client.patch(
        f"/api/v1/acordes/{acorde['id']}",
        json={"nombre": "Fresco especiado"},
    )
    assert response.status_code == 200
    assert response.json()["slug"] == "fresco-especiado"

    response = client.patch(f"/api/v1/acordes/{acorde['id']}", json={"slug": ""})
    assert response.status_code == 200
    assert response.json()["slug"] == "fresco-especiado"

    response = client.delete(f"/api/v1/acordes/{acorde['id']}")
    assert response.status_code == 200
    assert response.json()["activo"] is False

    response = client.get("/api/v1/acordes")
    assert response.status_code == 200
    assert response.json()["total"] == 0

    response = client.get("/api/v1/acordes", params={"activo": "false"})
    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == acorde["id"]


def test_acorde_duplicado_ignora_mayusculas_y_acentos(client):
    response = client.post("/api/v1/acordes", json={"nombre": "\u00c1mbar"})
    assert response.status_code == 201

    response = client.post("/api/v1/acordes", json={"nombre": "ambar"})
    assert response.status_code == 409
    assert response.json()["detail"] == "Ya existe un acorde con ese slug."


def test_acorde_inexistente(client):
    response = client.get("/api/v1/acordes/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Acorde no encontrado."


def test_permisos_acordes(client, public_client, vendedor_headers):
    acorde = client.post("/api/v1/acordes", json={"nombre": "Marino"}).json()

    response = public_client.get("/api/v1/acordes")
    assert response.status_code == 401

    response = client.get("/api/v1/acordes", headers=vendedor_headers)
    assert response.status_code == 200

    response = client.post(
        "/api/v1/acordes",
        json={"nombre": "Aromatico"},
        headers=vendedor_headers,
    )
    assert response.status_code == 403

    response = client.patch(
        f"/api/v1/acordes/{acorde['id']}",
        json={"nombre": "Acuatico"},
        headers=vendedor_headers,
    )
    assert response.status_code == 403

    response = client.delete(
        f"/api/v1/acordes/{acorde['id']}",
        headers=vendedor_headers,
    )
    assert response.status_code == 403
