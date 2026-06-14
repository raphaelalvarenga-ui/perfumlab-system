import sys
from pathlib import Path
from time import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.controllers.inventario_controller import InventarioController
from app.controllers.productos_controller import ProductosController
from app.database.conexion import inicializar_base_datos
from app.models.producto import Producto


def verificar_stock(productos_controller, producto_id, stock_esperado):
    producto = productos_controller.obtener_producto(producto_id)

    if producto.stock_actual != stock_esperado:
        raise AssertionError(
            f"Stock esperado: {stock_esperado}. Stock obtenido: {producto.stock_actual}."
        )

    print(f"Stock verificado: {producto.stock_actual}")


def mostrar_movimientos(movimientos, producto_id):
    print("\nMovimientos de inventario:")

    for movimiento in movimientos:
        if movimiento["producto_id"] == producto_id:
            print(
                f"{movimiento['id']} | {movimiento['tipo_movimiento']} | "
                f"Cantidad: {movimiento['cantidad']} | "
                f"{movimiento['stock_anterior']} -> {movimiento['stock_nuevo']} | "
                f"Motivo: {movimiento['motivo']} | Fecha: {movimiento['fecha']}"
            )


def main():
    inicializar_base_datos()

    productos_controller = ProductosController()
    inventario_controller = InventarioController()
    producto_id = None

    try:
        producto = Producto(
            sku=f"TEST-INV-{int(time())}",
            nombre="Producto prueba inventario",
            marca="Perfum Lab",
            descripcion="Producto temporal para probar movimientos de inventario",
            costo=100,
            precio=150,
            stock_actual=10,
            stock_minimo=2,
        )

        producto_id = productos_controller.crear_producto(producto)
        print(f"Producto de prueba creado con ID {producto_id}")
        verificar_stock(productos_controller, producto_id, 10)

        inventario_controller.registrar_entrada(
            producto_id,
            20,
            "Entrada de prueba local",
        )
        verificar_stock(productos_controller, producto_id, 30)

        inventario_controller.registrar_salida(
            producto_id,
            5,
            "Salida de prueba local",
        )
        verificar_stock(productos_controller, producto_id, 25)

        inventario_controller.registrar_ajuste(
            producto_id,
            50,
            "Ajuste de prueba local",
        )
        verificar_stock(productos_controller, producto_id, 50)

        movimientos = inventario_controller.obtener_movimientos()
        mostrar_movimientos(movimientos, producto_id)

        print("\nPrueba de inventario completada correctamente.")
    finally:
        if producto_id is not None:
            productos_controller.eliminar_producto(producto_id)
            print(f"Producto de prueba desactivado: {producto_id}")


if __name__ == "__main__":
    main()
