import tkinter as tk
from tkinter import ttk

from app.database.conexion import inicializar_base_datos, obtener_conexion


def obtener_resumen_reportes():
    inicializar_base_datos()

    with obtener_conexion() as conexion:
        ventas = conexion.execute(
            """
            SELECT
                COUNT(*) AS cantidad_ventas,
                COALESCE(SUM(total), 0) AS total_ventas
            FROM ventas
            WHERE estado = 'Completada'
            """
        ).fetchone()

        facturas = conexion.execute(
            """
            SELECT
                COUNT(*) AS cantidad_facturas,
                COALESCE(SUM(total), 0) AS total_facturado
            FROM facturas
            """
        ).fetchone()

        productos_bajo_stock = conexion.execute(
            """
            SELECT COUNT(*) AS total
            FROM productos
            WHERE activo = 1 AND stock_actual <= stock_minimo
            """
        ).fetchone()

    return {
        "cantidad_ventas": ventas["cantidad_ventas"],
        "total_ventas": ventas["total_ventas"],
        "cantidad_facturas": facturas["cantidad_facturas"],
        "total_facturado": facturas["total_facturado"],
        "productos_bajo_stock": productos_bajo_stock["total"],
    }


def obtener_productos_bajo_stock():
    inicializar_base_datos()

    with obtener_conexion() as conexion:
        return conexion.execute(
            """
            SELECT id, sku, nombre, stock_actual, stock_minimo
            FROM productos
            WHERE activo = 1 AND stock_actual <= stock_minimo
            ORDER BY nombre ASC
            """
        ).fetchall()


def abrir_reportes(ventana=None):
    ventana = ventana or tk.Toplevel()
    ventana.title("Reportes")
    ventana.geometry("760x460")

    frame = ttk.Frame(ventana, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(2, weight=1)

    resumen_var = tk.StringVar()
    ttk.Label(frame, textvariable=resumen_var, justify=tk.LEFT).grid(
        row=0,
        column=0,
        sticky=tk.W,
        pady=(0, 10),
    )

    columnas = ("id", "sku", "nombre", "stock_actual", "stock_minimo")
    tabla = ttk.Treeview(frame, columns=columnas, show="headings")
    encabezados = {
        "id": "ID",
        "sku": "SKU",
        "nombre": "Producto",
        "stock_actual": "Stock actual",
        "stock_minimo": "Stock minimo",
    }

    for columna in columnas:
        tabla.heading(columna, text=encabezados[columna])
        tabla.column(columna, width=130, anchor=tk.W)

    scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tabla.yview)
    tabla.configure(yscrollcommand=scroll.set)
    tabla.grid(row=2, column=0, sticky="nsew")
    scroll.grid(row=2, column=1, sticky="ns")

    def cargar_reportes():
        resumen = obtener_resumen_reportes()
        resumen_var.set(
            "Resumen general\n"
            f"Ventas completadas: {resumen['cantidad_ventas']}\n"
            f"Total ventas: L {resumen['total_ventas']:.2f}\n"
            f"Facturas emitidas: {resumen['cantidad_facturas']}\n"
            f"Total facturado: L {resumen['total_facturado']:.2f}\n"
            f"Productos bajo stock: {resumen['productos_bajo_stock']}"
        )

        for item in tabla.get_children():
            tabla.delete(item)

        for producto in obtener_productos_bajo_stock():
            tabla.insert(
                "",
                tk.END,
                values=tuple(producto[columna] for columna in columnas),
            )

    ttk.Button(frame, text="Actualizar reportes", command=cargar_reportes).grid(
        row=1,
        column=0,
        sticky=tk.E,
        pady=(0, 8),
    )
    cargar_reportes()
