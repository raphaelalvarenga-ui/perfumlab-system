from app.controllers.productos_controller import ProductosController
from app.models.producto import Producto

from .conftest import json_response


def producto_response(**overrides):
    data = {
        "id": 10,
        "sku": "API-001",
        "nombre": "Producto API",
        "marca": "Marca",
        "descripcion": "",
        "categoria_id": 3,
        "costo": "10.00",
        "precio": "20.00",
        "stock_actual": 5,
        "stock_minimo": 1,
        "activo": True,
    }
    data.update(overrides)
    return data


def test_listar_obtener_crear_actualizar_eliminar_y_buscar(make_api_client):
    requests = []

    def handler(request):
        requests.append(request)
        if request.method == "GET" and request.url.path == "/api/v1/productos":
            return json_response(
                200,
                {
                    "items": [producto_response()],
                    "page": 1,
                    "limit": 100,
                    "total": 1,
                    "pages": 1,
                },
            )
        if request.method == "GET":
            return json_response(200, producto_response())
        if request.method == "POST":
            return json_response(201, producto_response(id=11))
        if request.method == "PATCH":
            return json_response(200, producto_response(nombre="Editado"))
        if request.method == "DELETE":
            return json_response(200, producto_response(activo=False))
        raise AssertionError(request)

    client = make_api_client(handler)

    assert client.productos.listar_todos(buscar="api")[0]["id"] == 10
    assert client.productos.obtener(10)["sku"] == "API-001"
    assert client.productos.crear({"sku": "API-002"})["id"] == 11
    assert client.productos.actualizar(10, {"nombre": "Editado"})["nombre"] == "Editado"
    assert not client.productos.eliminar(10)["activo"]
    assert requests[0].url.params["buscar"] == "api"


def test_controller_update_does_not_send_stock_actual(make_api_client):
    captured = {}

    def handler(request):
        captured["json"] = request.read().decode()
        return json_response(200, producto_response())

    client = make_api_client(handler)
    controller = ProductosController(api_client=client)
    producto = Producto(
        sku="API-001",
        nombre="Producto API",
        marca="Marca",
        categoria_id=3,
        costo=10,
        precio=20,
        stock_actual=999,
        stock_minimo=2,
    )

    assert controller.actualizar_producto(10, producto)
    assert "stock_actual" not in captured["json"]
    assert "categoria_id" in captured["json"]


def test_controller_create_allows_initial_stock(make_api_client):
    captured = {}

    def handler(request):
        captured["json"] = request.read().decode()
        return json_response(201, producto_response(id=12))

    client = make_api_client(handler)
    controller = ProductosController(api_client=client)
    producto = Producto(
        sku="API-NEW",
        nombre="Producto Nuevo",
        categoria_id=3,
        costo=10,
        precio=20,
        stock_actual=7,
        stock_minimo=1,
    )

    assert controller.crear_producto(producto) == 12
    assert "stock_actual" in captured["json"]
