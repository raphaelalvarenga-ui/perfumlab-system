from app.database.conexion import crear_tablas
from app.ventas.ventas import crear_tabla_ventas
from app.facturas.facturas import crear_tabla_facturas


def main():
    crear_tablas()
    crear_tabla_ventas()
    crear_tabla_facturas()

    print("Archivos JSON creados correctamente.")


if __name__ == "__main__":
    main()
