import tempfile
import unittest
from pathlib import Path

from app.controllers.inventario_controller import InventarioController
from app.controllers.productos_controller import ProductosController
from app.database.json_storage import cargar_tabla, inicializar_datos_json
from app.facturas import facturas
from app.models.categoria import Categoria
from app.models.producto import Producto
from app.reportes import reportes
from app.ventas import ventas


class PerfumLabQATestCase(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.ruta_db = Path(self.temporal.name) / "json"
        inicializar_datos_json(self.ruta_db)
        self.productos = ProductosController(self.ruta_db)
        self.inventario = InventarioController(self.ruta_db)

    def tearDown(self):
        self.temporal.cleanup()

    def _producto(self, producto_id):
        return self.productos.obtener_producto(producto_id)

    def test_productos_e_inventario_crud_y_movimientos(self):
        producto = Producto(
            sku="QA-INV-001",
            nombre="QA Inventario",
            marca="Perfum Lab",
            descripcion="Producto temporal de QA",
            costo=100,
            precio=180,
            stock_actual=10,
            stock_minimo=3,
        )

        producto_id = self.productos.crear_producto(producto)
        self.assertEqual(self._producto(producto_id).stock_actual, 10)

        with self.assertRaises(ValueError):
            self.productos.crear_producto(
                Producto(
                    sku=" qa-inv-001 ",
                    nombre="SKU duplicado",
                    costo=1,
                    precio=2,
                )
            )

        encontrados = self.productos.buscar_productos("qa inventario")
        self.assertTrue(any(producto.id == producto_id for producto in encontrados))

        self.inventario.registrar_entrada(producto_id, 5, "Entrada QA")
        self.assertEqual(self._producto(producto_id).stock_actual, 15)

        self.inventario.registrar_salida(producto_id, 4, "Salida QA")
        self.assertEqual(self._producto(producto_id).stock_actual, 11)

        with self.assertRaises(ValueError):
            self.inventario.registrar_salida(producto_id, 99, "Salida excesiva")
        self.assertEqual(self._producto(producto_id).stock_actual, 11)

        self.inventario.registrar_ajuste(producto_id, 7, "Ajuste QA")
        self.assertEqual(self._producto(producto_id).stock_actual, 7)

        movimientos = self.inventario.obtener_movimientos(producto_id)
        self.assertEqual(
            [movimiento["tipo_movimiento"] for movimiento in movimientos[:3]],
            ["AJUSTE", "SALIDA", "ENTRADA"],
        )

        self.assertTrue(self.productos.eliminar_producto(producto_id))
        activos = self.productos.listar_productos()
        self.assertFalse(any(producto.id == producto_id for producto in activos))
        self.assertFalse(self._producto(producto_id).activo)

    def test_venta_multiple_factura_exports_y_bloqueo_de_anulacion(self):
        stock_producto_1 = self._producto(1).stock_actual
        stock_producto_2 = self._producto(2).stock_actual

        ok, mensaje = ventas.registrar_venta_multiple(
            "Cliente QA",
            [
                {"producto_id": 1, "cantidad": 2},
                {"producto_id": "2", "cantidad": "1"},
            ],
            ruta_db=self.ruta_db,
        )

        self.assertTrue(ok, mensaje)
        venta = ventas.obtener_ventas(self.ruta_db)[0]
        self.assertEqual(venta["cliente"], "Cliente QA")
        self.assertEqual(venta["cantidad"], 3)
        self.assertAlmostEqual(venta["total"], 2480.0)
        self.assertEqual(self._producto(1).stock_actual, stock_producto_1 - 2)
        self.assertEqual(self._producto(2).stock_actual, stock_producto_2 - 1)

        detalle = ventas.obtener_detalle_venta(venta["id"], self.ruta_db)
        self.assertEqual(len(detalle), 2)
        self.assertEqual(sum(item["cantidad"] for item in detalle), 3)

        ventas_pendientes = facturas.obtener_ventas_para_facturar(self.ruta_db)
        self.assertTrue(any(item["id"] == venta["id"] for item in ventas_pendientes))

        ok, mensaje = facturas.generar_factura(venta["id"], self.ruta_db)
        self.assertTrue(ok, mensaje)
        factura = facturas.obtener_factura_por_venta_id(venta["id"], self.ruta_db)
        self.assertEqual(factura["numero_factura"], "FAC-000001")

        ok, mensaje = facturas.generar_factura(venta["id"], self.ruta_db)
        self.assertFalse(ok)
        self.assertIn("ya tiene factura", mensaje)

        ventas_pendientes = facturas.obtener_ventas_para_facturar(self.ruta_db)
        self.assertFalse(any(item["id"] == venta["id"] for item in ventas_pendientes))

        ok, mensaje = ventas.anular_venta(venta["id"], self.ruta_db)
        self.assertFalse(ok)
        self.assertIn("ya tiene factura", mensaje)

        texto = facturas.generar_texto_factura(factura["id"], self.ruta_db)
        self.assertIn("FAC-000001", texto)
        self.assertIn("TOTAL", texto)

        ruta_txt = Path(self.temporal.name) / "factura.txt"
        facturas.exportar_factura_txt(factura["id"], ruta_txt, self.ruta_db)
        self.assertIn("Cliente QA", ruta_txt.read_text(encoding="utf-8"))

        ruta_pdf = Path(self.temporal.name) / "factura.pdf"
        facturas.exportar_factura_pdf(factura["id"], ruta_pdf, self.ruta_db)
        self.assertTrue(ruta_pdf.read_bytes().startswith(b"%PDF-"))

    def test_anular_venta_devuelve_stock_y_excluye_facturacion(self):
        stock_inicial = self._producto(3).stock_actual

        ok, mensaje = ventas.registrar_venta(
            3,
            "Cliente anulacion QA",
            2,
            ruta_db=self.ruta_db,
        )
        self.assertTrue(ok, mensaje)
        venta = ventas.obtener_ventas(self.ruta_db)[0]
        self.assertEqual(self._producto(3).stock_actual, stock_inicial - 2)

        ok, mensaje = ventas.anular_venta(venta["id"], self.ruta_db)
        self.assertTrue(ok, mensaje)
        self.assertEqual(self._producto(3).stock_actual, stock_inicial)
        self.assertEqual(
            ventas.buscar_venta_por_id(venta["id"], self.ruta_db)["estado"],
            "Anulada",
        )

        ok, mensaje = facturas.generar_factura(venta["id"], self.ruta_db)
        self.assertFalse(ok)
        self.assertIn("Solo se pueden facturar ventas completadas", mensaje)
        self.assertFalse(facturas.obtener_ventas_para_facturar(self.ruta_db))

    def test_validaciones_de_venta_no_modifican_datos(self):
        ventas_antes = len(cargar_tabla("ventas", self.ruta_db))
        movimientos_antes = len(cargar_tabla("movimientos_inventario", self.ruta_db))
        stock_inicial = self._producto(2).stock_actual

        casos = [
            ventas.registrar_venta(2, "", 1, ruta_db=self.ruta_db),
            ventas.registrar_venta(2, "Cliente QA", 0, ruta_db=self.ruta_db),
            ventas.registrar_venta(
                2,
                "Cliente QA",
                stock_inicial + 1,
                ruta_db=self.ruta_db,
            ),
        ]

        self.assertTrue(all(not ok for ok, _mensaje in casos))
        self.assertEqual(len(cargar_tabla("ventas", self.ruta_db)), ventas_antes)
        self.assertEqual(
            len(cargar_tabla("movimientos_inventario", self.ruta_db)),
            movimientos_antes,
        )
        self.assertEqual(self._producto(2).stock_actual, stock_inicial)

    def test_validaciones_de_formato_y_campos_requeridos(self):
        productos_invalidos = [
            Producto(
                sku="AB",
                nombre="Producto valido",
                costo=1,
                precio=2,
            ),
            Producto(
                sku="SKU CON ESPACIO",
                nombre="Producto valido",
                costo=1,
                precio=2,
            ),
            Producto(
                sku="QA-VAL-001",
                nombre="1",
                costo=1,
                precio=2,
            ),
            Producto(
                sku="QA-VAL-002",
                nombre="Producto valido",
                costo=1,
                precio=float("nan"),
            ),
        ]

        for producto in productos_invalidos:
            with self.subTest(sku=producto.sku, nombre=producto.nombre):
                with self.assertRaises(ValueError):
                    self.productos.crear_producto(producto)

        with self.assertRaises(ValueError):
            self.productos.crear_categoria(Categoria(nombre="1"))

        ventas_invalidas = [
            ventas.registrar_venta(0, "Cliente QA", 1, ruta_db=self.ruta_db),
            ventas.registrar_venta(1, "12345", 1, ruta_db=self.ruta_db),
            ventas.registrar_venta(1, "Cliente QA", "1.5", ruta_db=self.ruta_db),
        ]
        self.assertTrue(all(not ok for ok, _mensaje in ventas_invalidas))

        ok, mensaje = facturas.generar_factura("ABC", self.ruta_db)
        self.assertFalse(ok)
        self.assertIn("ID de venta", mensaje)

        with self.assertRaises(ValueError):
            reportes.obtener_resumen_reportes("2026/08/03", ruta_db=self.ruta_db)

        with self.assertRaises(ValueError):
            reportes.obtener_ventas_recientes(
                "2026-12-31",
                "2026-01-01",
                self.ruta_db,
            )

        with self.assertRaises(ValueError):
            facturas.exportar_factura_pdf(
                1,
                Path(self.temporal.name) / "factura.txt",
                self.ruta_db,
            )

        with self.assertRaises(ValueError):
            reportes.exportar_csv(
                Path(self.temporal.name) / "reporte.txt",
                [],
                ("id",),
                {"id": "ID"},
            )

    def test_items_repetidos_se_agrupan_en_una_sola_linea(self):
        stock_inicial = self._producto(4).stock_actual

        ok, mensaje = ventas.registrar_venta_multiple(
            "Cliente repetidos QA",
            [
                {"producto_id": 4, "cantidad": 1},
                {"producto_id": 4, "cantidad": 2},
            ],
            ruta_db=self.ruta_db,
        )

        self.assertTrue(ok, mensaje)
        venta = ventas.obtener_ventas(self.ruta_db)[0]
        detalle = ventas.obtener_detalle_venta(venta["id"], self.ruta_db)
        self.assertEqual(len(detalle), 1)
        self.assertEqual(detalle[0]["cantidad"], 3)
        self.assertAlmostEqual(detalle[0]["subtotal"], 2460.0)
        self.assertEqual(self._producto(4).stock_actual, stock_inicial - 3)

    def test_reportes_resumen_productos_mas_vendidos_y_csv(self):
        ok, mensaje = ventas.registrar_venta(
            1,
            "Cliente reportes QA",
            2,
            ruta_db=self.ruta_db,
        )
        self.assertTrue(ok, mensaje)
        venta_facturada = ventas.obtener_ventas(self.ruta_db)[0]
        ok, mensaje = facturas.generar_factura(venta_facturada["id"], self.ruta_db)
        self.assertTrue(ok, mensaje)

        ok, mensaje = ventas.registrar_venta(
            3,
            "Cliente anulada reporte QA",
            1,
            ruta_db=self.ruta_db,
        )
        self.assertTrue(ok, mensaje)
        venta_anulada = ventas.obtener_ventas(self.ruta_db)[0]
        ok, mensaje = ventas.anular_venta(venta_anulada["id"], self.ruta_db)
        self.assertTrue(ok, mensaje)

        resumen = reportes.obtener_resumen_reportes(ruta_db=self.ruta_db)
        self.assertEqual(resumen["cantidad_ventas"], 1)
        self.assertAlmostEqual(resumen["total_ventas"], 1700.0)
        self.assertEqual(resumen["cantidad_facturas"], 1)
        self.assertAlmostEqual(resumen["total_facturado"], 1700.0)
        self.assertGreaterEqual(resumen["productos_bajo_stock"], 1)

        resumen_vacio = reportes.obtener_resumen_reportes(
            "1900-01-01",
            "1900-01-02",
            self.ruta_db,
        )
        self.assertEqual(resumen_vacio["cantidad_ventas"], 0)
        self.assertEqual(resumen_vacio["cantidad_facturas"], 0)

        mas_vendidos = reportes.obtener_productos_mas_vendidos(ruta_db=self.ruta_db)
        self.assertEqual(mas_vendidos[0]["id"], 1)
        self.assertEqual(mas_vendidos[0]["cantidad_vendida"], 2)

        ventas_recientes = reportes.obtener_ventas_recientes(ruta_db=self.ruta_db)
        self.assertEqual(len(ventas_recientes), 2)
        self.assertEqual(ventas_recientes[0]["estado"], "Anulada")

        bajo_stock = reportes.obtener_productos_bajo_stock(self.ruta_db)
        self.assertTrue(all(item["stock_actual"] <= item["stock_minimo"] for item in bajo_stock))

        ruta_csv = Path(self.temporal.name) / "mas_vendidos.csv"
        reportes.exportar_csv(
            ruta_csv,
            mas_vendidos,
            ("id", "sku", "nombre", "cantidad_vendida", "total_vendido"),
            {
                "id": "ID",
                "sku": "SKU",
                "nombre": "Producto",
                "cantidad_vendida": "Cantidad vendida",
                "total_vendido": "Total vendido",
            },
        )
        contenido_csv = ruta_csv.read_text(encoding="utf-8")
        self.assertIn("Cantidad vendida", contenido_csv)
        self.assertIn("Cedro Nocturno", contenido_csv)


if __name__ == "__main__":
    unittest.main()
