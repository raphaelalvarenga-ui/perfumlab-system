def test_crear_listar_buscar_obtener_actualizar_y_soft_delete_nota(client):
    response = client.post(
        "/api/v1/notas",
        json={"nombre": " Toronja ", "imagen_url": ""},
    )
    assert response.status_code == 201
    nota = response.json()
    assert nota["nombre"] == "Toronja"
    assert nota["slug"] == "toronja"
    assert nota["imagen_url"] is None

    response = client.get("/api/v1/notas", params={"buscar": "toronja"})
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = client.get(f"/api/v1/notas/{nota['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == nota["id"]

    response = client.patch(
        f"/api/v1/notas/{nota['id']}",
        json={
            "nombre": "Madera de gaiac",
            "imagen_url": "https://example.test/gaiac.png",
        },
    )
    assert response.status_code == 200
    assert response.json()["slug"] == "madera-de-gaiac"
    assert response.json()["imagen_url"] == "https://example.test/gaiac.png"

    response = client.patch(f"/api/v1/notas/{nota['id']}", json={"slug": ""})
    assert response.status_code == 200
    assert response.json()["slug"] == "madera-de-gaiac"

    response = client.delete(f"/api/v1/notas/{nota['id']}")
    assert response.status_code == 200
    assert response.json()["activo"] is False

    response = client.get("/api/v1/notas")
    assert response.status_code == 200
    assert response.json()["total"] == 0

    response = client.get("/api/v1/notas", params={"activo": "false"})
    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == nota["id"]


def test_nota_duplicada_ignora_mayusculas_y_acentos(client):
    response = client.post("/api/v1/notas", json={"nombre": "\u00c1mbar gris"})
    assert response.status_code == 201

    response = client.post("/api/v1/notas", json={"nombre": "ambar gris"})
    assert response.status_code == 409
    assert response.json()["detail"] == "Ya existe una nota con ese slug."


def test_nota_inexistente(client):
    response = client.get("/api/v1/notas/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Nota no encontrada."


def test_permisos_notas(client, public_client, vendedor_headers):
    nota = client.post("/api/v1/notas", json={"nombre": "Laurel"}).json()

    response = public_client.get("/api/v1/notas")
    assert response.status_code == 401

    response = client.get("/api/v1/notas", headers=vendedor_headers)
    assert response.status_code == 200

    response = client.post(
        "/api/v1/notas",
        json={"nombre": "Mandarina"},
        headers=vendedor_headers,
    )
    assert response.status_code == 403

    response = client.patch(
        f"/api/v1/notas/{nota['id']}",
        json={"nombre": "Pimienta rosa"},
        headers=vendedor_headers,
    )
    assert response.status_code == 403

    response = client.delete(f"/api/v1/notas/{nota['id']}", headers=vendedor_headers)
    assert response.status_code == 403
