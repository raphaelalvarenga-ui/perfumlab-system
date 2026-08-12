def crear_categoria(client, nombre="Perfumes"):
    response = client.post("/api/v1/categorias", json={"nombre": nombre})
    assert response.status_code == 201
    return response.json()


def crear_producto(client, categoria_id, **overrides):
    data = {
        "sku": "PERF-OLF-001",
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
        "concentracion": "EDT",
        "duracion": "Long lasting",
        "estela": "Strong",
    }
    data.update(overrides)
    response = client.post("/api/v1/productos", json=data)
    assert response.status_code == 201
    return response.json()


def crear_acorde(client, nombre):
    response = client.post("/api/v1/acordes", json={"nombre": nombre})
    assert response.status_code == 201
    return response.json()


def crear_nota(client, nombre):
    response = client.post("/api/v1/notas", json={"nombre": nombre})
    assert response.status_code == 201
    return response.json()


def test_perfil_olfativo_vacio_y_reemplazo_completo(client, vendedor_headers):
    categoria = crear_categoria(client)
    producto = crear_producto(client, categoria["id"])
    citrico = crear_acorde(client, "C\u00edtrico")
    marino = crear_acorde(client, "Marino")
    aromatico = crear_acorde(client, "Aromatico")
    amaderado = crear_acorde(client, "Amaderado")
    toronja = crear_nota(client, "Toronja")
    mandarina = crear_nota(client, "Mandarina")
    notas_marinas = crear_nota(client, "Notas marinas")
    laurel = crear_nota(client, "Laurel")
    ambar_gris = crear_nota(client, "\u00c1mbar gris")
    gaiac = crear_nota(client, "Madera de gaiac")

    response = client.get(f"/api/v1/productos/{producto['id']}/perfil-olfativo")
    assert response.status_code == 200
    assert response.json() == {
        "producto_id": producto["id"],
        "acordes": [],
        "notas": {"salida": [], "corazon": [], "fondo": []},
    }

    response = client.get(
        f"/api/v1/productos/{producto['id']}/perfil-olfativo",
        headers=vendedor_headers,
    )
    assert response.status_code == 200

    payload = {
        "acordes": [
            {
                "acorde_id": citrico["id"],
                "intensidad": "DOMINANTE",
                "posicion": 0,
            },
            {"acorde_id": marino["id"], "intensidad": "DOMINANTE", "posicion": 1},
            {
                "acorde_id": aromatico["id"],
                "intensidad": "PROMINENTE",
                "posicion": 2,
            },
            {
                "acorde_id": amaderado["id"],
                "intensidad": "MODERADO",
                "posicion": 3,
            },
        ],
        "notas": [
            {"nota_id": toronja["id"], "tipo": "SALIDA", "posicion": 0},
            {"nota_id": mandarina["id"], "tipo": "SALIDA", "posicion": 1},
            {"nota_id": notas_marinas["id"], "tipo": "CORAZON", "posicion": 0},
            {"nota_id": laurel["id"], "tipo": "CORAZON", "posicion": 1},
            {"nota_id": ambar_gris["id"], "tipo": "FONDO", "posicion": 0},
            {"nota_id": gaiac["id"], "tipo": "FONDO", "posicion": 1},
        ],
    }
    response = client.put(
        f"/api/v1/productos/{producto['id']}/perfil-olfativo",
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert [item["slug"] for item in data["acordes"]] == [
        "citrico",
        "marino",
        "aromatico",
        "amaderado",
    ]
    assert data["acordes"][0]["intensidad"] == "DOMINANTE"
    assert [item["nombre"] for item in data["notas"]["salida"]] == [
        "Toronja",
        "Mandarina",
    ]
    assert [item["nombre"] for item in data["notas"]["corazon"]] == [
        "Notas marinas",
        "Laurel",
    ]
    assert [item["slug"] for item in data["notas"]["fondo"]] == [
        "ambar-gris",
        "madera-de-gaiac",
    ]

    response = client.put(
        f"/api/v1/productos/{producto['id']}/perfil-olfativo",
        json={"acordes": [], "notas": []},
        headers=vendedor_headers,
    )
    assert response.status_code == 403


def test_reemplazo_de_perfil_es_total(client):
    categoria = crear_categoria(client)
    producto = crear_producto(client, categoria["id"])
    citrico = crear_acorde(client, "Citrico")
    dulce = crear_acorde(client, "Dulce")
    toronja = crear_nota(client, "Toronja")
    vainilla = crear_nota(client, "Vainilla")

    response = client.put(
        f"/api/v1/productos/{producto['id']}/perfil-olfativo",
        json={
            "acordes": [{"acorde_id": citrico["id"], "posicion": 0}],
            "notas": [{"nota_id": toronja["id"], "tipo": "SALIDA", "posicion": 0}],
        },
    )
    assert response.status_code == 200

    response = client.put(
        f"/api/v1/productos/{producto['id']}/perfil-olfativo",
        json={
            "acordes": [{"acorde_id": dulce["id"], "posicion": 0}],
            "notas": [{"nota_id": vainilla["id"], "tipo": "FONDO", "posicion": 0}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert [item["slug"] for item in data["acordes"]] == ["dulce"]
    assert data["notas"]["salida"] == []
    assert [item["slug"] for item in data["notas"]["fondo"]] == ["vainilla"]


def test_perfil_valida_referencias_duplicados_inactivos_y_producto_inactivo(client):
    categoria = crear_categoria(client)
    producto = crear_producto(client, categoria["id"])
    acorde = crear_acorde(client, "Marino")
    nota = crear_nota(client, "Laurel")
    acorde_inactivo = crear_acorde(client, "Aromatico")
    nota_inactiva = crear_nota(client, "Mandarina")
    assert client.delete(f"/api/v1/acordes/{acorde_inactivo['id']}").status_code == 200
    assert client.delete(f"/api/v1/notas/{nota_inactiva['id']}").status_code == 200

    casos = [
        (
            {"acordes": [{"acorde_id": acorde["id"]}, {"acorde_id": acorde["id"]}]},
            409,
            "El perfil no puede repetir acordes.",
        ),
        (
            {
                "notas": [
                    {"nota_id": nota["id"], "tipo": "SALIDA"},
                    {"nota_id": nota["id"], "tipo": "SALIDA"},
                ]
            },
            409,
            "El perfil no puede repetir la misma nota y tipo.",
        ),
        ({"acordes": [{"acorde_id": 999}]}, 404, "Acorde no encontrado."),
        (
            {"notas": [{"nota_id": 999, "tipo": "SALIDA"}]},
            404,
            "Nota no encontrada.",
        ),
        (
            {"acordes": [{"acorde_id": acorde_inactivo["id"]}]},
            409,
            "No se puede usar un acorde inactivo.",
        ),
        (
            {"notas": [{"nota_id": nota_inactiva["id"], "tipo": "SALIDA"}]},
            409,
            "No se puede usar una nota inactiva.",
        ),
    ]
    for payload, status_code, detail in casos:
        response = client.put(
            f"/api/v1/productos/{producto['id']}/perfil-olfativo",
            json=payload,
        )
        assert response.status_code == status_code
        assert response.json()["detail"] == detail

    response = client.put(
        "/api/v1/productos/999/perfil-olfativo",
        json={"acordes": [], "notas": []},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Producto no encontrado."

    assert client.delete(f"/api/v1/productos/{producto['id']}").status_code == 200
    response = client.get(f"/api/v1/productos/{producto['id']}/perfil-olfativo")
    assert response.status_code == 200

    response = client.put(
        f"/api/v1/productos/{producto['id']}/perfil-olfativo",
        json={"acordes": [], "notas": []},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == (
        "No se puede modificar el perfil olfativo de un producto inactivo."
    )


def test_reemplazo_de_perfil_es_atomico(client):
    categoria = crear_categoria(client)
    producto = crear_producto(client, categoria["id"])
    citrico = crear_acorde(client, "Citrico")
    dulce = crear_acorde(client, "Dulce")
    toronja = crear_nota(client, "Toronja")

    response = client.put(
        f"/api/v1/productos/{producto['id']}/perfil-olfativo",
        json={
            "acordes": [{"acorde_id": citrico["id"], "posicion": 0}],
            "notas": [{"nota_id": toronja["id"], "tipo": "SALIDA", "posicion": 0}],
        },
    )
    assert response.status_code == 200

    response = client.put(
        f"/api/v1/productos/{producto['id']}/perfil-olfativo",
        json={
            "acordes": [{"acorde_id": dulce["id"], "posicion": 0}],
            "notas": [{"nota_id": 999, "tipo": "FONDO", "posicion": 0}],
        },
    )
    assert response.status_code == 404

    response = client.get(f"/api/v1/productos/{producto['id']}/perfil-olfativo")
    assert response.status_code == 200
    data = response.json()
    assert [item["slug"] for item in data["acordes"]] == ["citrico"]
    assert [item["slug"] for item in data["notas"]["salida"]] == ["toronja"]
    assert data["notas"]["fondo"] == []


def test_productos_filtran_por_acorde_nota_tipo_y_paginacion(client):
    categoria = crear_categoria(client)
    invictus = crear_producto(
        client,
        categoria["id"],
        sku="PERF-FILTRO-001",
        nombre="Invictus",
        genero="Hombre",
    )
    good_girl = crear_producto(
        client,
        categoria["id"],
        sku="PERF-FILTRO-002",
        nombre="Good Girl",
        genero="Mujer",
    )
    fresco = crear_acorde(client, "Fresco especiado")
    dulce = crear_acorde(client, "Dulce")
    toronja = crear_nota(client, "Toronja")
    laurel = crear_nota(client, "Laurel")

    assert client.put(
        f"/api/v1/productos/{invictus['id']}/perfil-olfativo",
        json={
            "acordes": [{"acorde_id": fresco["id"], "posicion": 0}],
            "notas": [{"nota_id": toronja["id"], "tipo": "SALIDA", "posicion": 0}],
        },
    ).status_code == 200
    assert client.put(
        f"/api/v1/productos/{good_girl['id']}/perfil-olfativo",
        json={
            "acordes": [{"acorde_id": dulce["id"], "posicion": 0}],
            "notas": [{"nota_id": laurel["id"], "tipo": "CORAZON", "posicion": 0}],
        },
    ).status_code == 200

    response = client.get("/api/v1/productos", params={"acorde": "fresco-especiado"})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == invictus["id"]

    response = client.get("/api/v1/productos", params={"nota": "toronja"})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == invictus["id"]

    response = client.get(
        "/api/v1/productos",
        params={"nota": "laurel", "tipo_nota": "CORAZON"},
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == good_girl["id"]

    response = client.get(
        "/api/v1/productos",
        params={"nota": "laurel", "tipo_nota": "SALIDA"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0

    response = client.get(
        "/api/v1/productos",
        params={
            "acorde": "fresco-especiado",
            "nota": "toronja",
            "page": 1,
            "limit": 1,
        },
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["pages"] == 1
