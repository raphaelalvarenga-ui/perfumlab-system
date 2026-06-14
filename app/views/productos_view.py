from app.controllers.productos_controller import ProductosController
from app.models.producto import Producto


class ProductosView:
    def __init__(self, controller=None):
        self.controller = controller or ProductosController()

    def mostrar_productos(self):
        productos = self.controller.listar_productos()

        for producto in productos:
            print(
                f"{producto.id} | {producto.sku} | {producto.nombre} | "
                f"Stock: {producto.stock_actual} | Precio: {producto.precio:.2f}"
            )

    def crear_producto_basico(self):
        producto = Producto(
            sku=input("SKU: "),
            nombre=input("Nombre: "),
            marca=input("Marca: "),
            descripcion=input("Descripcion: "),
            costo=float(input("Costo: ") or 0),
            precio=float(input("Precio: ") or 0),
            stock_actual=int(input("Stock actual: ") or 0),
            stock_minimo=int(input("Stock minimo: ") or 0),
        )

        producto_id = self.controller.crear_producto(producto)
        print(f"Producto guardado con ID {producto_id}.")
