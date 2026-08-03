import sys
from pathlib import Path
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database.json_storage import inicializar_datos_json
from app.facturas import facturas
from app.reportes import reportes
from app.ventas import ventas


def asegurar(condicion, mensaje):
    if not condicion:
        raise AssertionError(mensaje)


def main():
    with TemporaryDirectory() as temporal:
        ruta_db = Path(temporal) / "json"
        inicializar_datos_json(ruta_db)

        ok, mensaje = ventas.registrar_venta_multiple(
            "Cliente QA Smoke",
            [
                {"producto_id": 1, "cantidad": 2},
                {"producto_id": 2, "cantidad": 1},
            ],
            ruta_db=ruta_db,
        )
        asegurar(ok, mensaje)

        venta = ventas.obtener_ventas(ruta_db)[0]
        asegurar(venta["cantidad"] == 3, "La venta no registro todas las unidades.")
        asegurar(venta["total"] == 2480.0, "El total de la venta no coincide.")

        ok, mensaje = facturas.generar_factura(venta["id"], ruta_db=ruta_db)
        asegurar(ok, mensaje)

        factura = facturas.obtener_factura_por_venta_id(venta["id"], ruta_db)
        asegurar(factura is not None, "No se encontro la factura generada.")

        ruta_pdf = Path(temporal) / "factura_smoke.pdf"
        facturas.exportar_factura_pdf(factura["id"], ruta_pdf, ruta_db=ruta_db)
        asegurar(
            ruta_pdf.read_bytes().startswith(b"%PDF-"),
            "La factura PDF no tiene una cabecera valida.",
        )

        resumen = reportes.obtener_resumen_reportes(ruta_db=ruta_db)
        asegurar(resumen["cantidad_ventas"] == 1, "El reporte no conto la venta.")
        asegurar(resumen["cantidad_facturas"] == 1, "El reporte no conto la factura.")

        print("QA smoke OK")
        print(f"Venta generada: #{venta['id']} | Total: L {venta['total']:.2f}")
        print(f"Factura generada: {factura['numero_factura']}")


if __name__ == "__main__":
    main()
