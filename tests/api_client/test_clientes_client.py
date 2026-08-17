from app.controllers.clientes_controller import ClientesController
from app.models.cliente import Cliente

from .conftest import json_response


def cliente_response(**overrides):
    data = {
        "id": 5,
        "nombre": "Cliente API",
        "correo": None,
        "telefono": None,
        "direccion": None,
        "activo": True,
    }
    data.update(overrides)
    return data


def test_listar_obtener_crear_actualizar_eliminar_y_buscar(make_api_client):
    requests = []

    def handler(request):
        requests.append(request)
        if request.method == "GET" and request.url.path == "/api/v1/clientes":
            return json_response(
                200,
                {
                    "items": [cliente_response()],
                    "page": 1,
                    "limit": 100,
                    "total": 1,
                    "pages": 1,
                },
            )
        if request.method == "GET":
            return json_response(200, cliente_response())
        if request.method == "POST":
            return json_response(201, cliente_response(id=6))
        if request.method == "PATCH":
            return json_response(200, cliente_response(nombre="Editado"))
        if request.method == "DELETE":
            return json_response(200, cliente_response(activo=False))
        raise AssertionError(request)

    client = make_api_client(handler)

    assert client.clientes.listar_todos(buscar="api")[0]["id"] == 5
    assert client.clientes.obtener(5)["nombre"] == "Cliente API"
    assert client.clientes.crear({"nombre": "Nuevo"})["id"] == 6
    assert client.clientes.actualizar(5, {"nombre": "Editado"})["nombre"] == "Editado"
    assert not client.clientes.eliminar(5)["activo"]
    assert requests[0].url.params["buscar"] == "api"


def test_controller_sends_blank_email_as_null(make_api_client):
    captured = {}

    def handler(request):
        captured["json"] = request.content.decode()
        return json_response(201, cliente_response(id=7))

    client = make_api_client(handler)
    controller = ClientesController(api_client=client)

    assert controller.crear_cliente(Cliente(nombre="Cliente sin correo")) == 7
    assert '"correo":null' in captured["json"].replace(" ", "")
