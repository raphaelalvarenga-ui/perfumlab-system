def test_crear_listar_y_obtener_categoria(client):
    response = client.post("/api/v1/categorias", json={"nombre": " Hombre "})

    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Hombre"
    assert data["activo"] is True

    response = client.get("/api/v1/categorias")
    assert response.status_code == 200
    assert [item["nombre"] for item in response.json()] == ["Hombre"]

    response = client.get(f"/api/v1/categorias/{data['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == data["id"]


def test_actualizar_patch_y_soft_delete_categoria(client):
    categoria = client.post("/api/v1/categorias", json={"nombre": "Mujer"}).json()

    response = client.put(
        f"/api/v1/categorias/{categoria['id']}",
        json={"nombre": "Unisex", "activo": True},
    )
    assert response.status_code == 200
    assert response.json()["nombre"] == "Unisex"

    response = client.patch(
        f"/api/v1/categorias/{categoria['id']}",
        json={"nombre": "Ambientales"},
    )
    assert response.status_code == 200
    assert response.json()["nombre"] == "Ambientales"

    response = client.delete(f"/api/v1/categorias/{categoria['id']}")
    assert response.status_code == 200
    assert response.json()["activo"] is False

    response = client.get("/api/v1/categorias")
    assert response.status_code == 200
    assert response.json() == []


def test_categoria_inexistente(client):
    response = client.get("/api/v1/categorias/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Categoria no encontrada."


def test_categoria_duplicada_ignora_mayusculas(client):
    response = client.post("/api/v1/categorias", json={"nombre": "Hombre"})
    assert response.status_code == 201

    response = client.post("/api/v1/categorias", json={"nombre": "hombre"})

    assert response.status_code == 409
    assert response.json()["detail"] == "Ya existe una categoria con ese nombre."
