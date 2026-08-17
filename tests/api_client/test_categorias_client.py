from .conftest import json_response


def categoria_response(**overrides):
    data = {
        "id": 3,
        "nombre": "Categoria API",
        "activo": True,
    }
    data.update(overrides)
    return data


def test_listar_obtener_crear_actualizar_y_eliminar_categoria(make_api_client):
    requests = []

    def handler(request):
        requests.append(request)
        if request.method == "GET" and request.url.path == "/api/v1/categorias":
            return json_response(200, [categoria_response()])
        if request.method == "POST":
            return json_response(201, categoria_response(id=4))
        if request.method == "PATCH":
            return json_response(200, categoria_response(nombre="Editada"))
        if request.method == "DELETE":
            return json_response(200, categoria_response(activo=False))
        return json_response(200, categoria_response())

    client = make_api_client(handler)

    assert client.categorias.listar()[0]["id"] == 3
    assert client.categorias.obtener(3)["nombre"] == "Categoria API"
    assert client.categorias.crear({"nombre": "Nueva"})["id"] == 4
    assert client.categorias.actualizar(3, {"nombre": "Editada"})["nombre"] == "Editada"
    assert not client.categorias.eliminar(3)["activo"]
    assert [request.method for request in requests] == ["GET", "GET", "POST", "PATCH", "DELETE"]
