import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from app.database.conexion import inicializar_base_datos, obtener_conexion


def obtener_resumen_reportes(fecha_inicio=None, fecha_fin=None):
    inicializar_base_datos()
    filtro, parametros = _crear_filtro_fechas("ventas.fecha", fecha_inicio, fecha_fin)

    with obtener_conexion() as conexion:
        ventas = conexion.execute(
            f"""
            SELECT
                COUNT(*) AS cantidad_ventas,
                COALESCE(SUM(total), 0) AS total_ventas
            FROM ventas
            WHERE estado = 'Completada' {filtro}
            """,
            parametros,
        ).fetchone()

        facturas = conexion.execute(
            f"""
            SELECT
                COUNT(*) AS cantidad_facturas,
                COALESCE(SUM(facturas.total), 0) AS total_facturado
            FROM facturas
            INNER JOIN ventas ON ventas.id = facturas.venta_id
            WHERE ventas.estado = 'Completada' {filtro}
            """,
            parametros,
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
            ORDER BY stock_actual ASC, nombre ASC
            """
        ).fetchall()


def obtener_productos_mas_vendidos(fecha_inicio=None, fecha_fin=None):
    inicializar_base_datos()
    filtro, parametros = _crear_filtro_fechas("ventas.fecha", fecha_inicio, fecha_fin)

    with obtener_conexion() as conexion:
        return conexion.execute(
            f"""
            SELECT
                productos.id,
                productos.sku,
                productos.nombre,
                SUM(detalle_venta.cantidad) AS cantidad_vendida,
                SUM(detalle_venta.subtotal) AS total_vendido
            FROM detalle_venta
            INNER JOIN ventas ON ventas.id = detalle_venta.venta_id
            INNER JOIN productos ON productos.id = detalle_venta.producto_id
            WHERE ventas.estado = 'Completada' {filtro}
            GROUP BY productos.id, productos.sku, productos.nombre
            ORDER BY cantidad_vendida DESC, total_vendido DESC
            """,
            parametros,
        ).fetchall()


def obtener_ventas_recientes(fecha_inicio=None, fecha_fin=None):
    inicializar_base_datos()
    filtro, parametros = _crear_filtro_fechas("ventas.fecha", fecha_inicio, fecha_fin)

    with obtener_conexion() as conexion:
        return conexion.execute(
            f"""
            SELECT
                ventas.id,
                clientes.nombre AS cliente,
                ventas.total,
                ventas.estado,
                ventas.fecha
            FROM ventas
            LEFT JOIN clientes ON clientes.id = ventas.cliente_id
            WHERE 1 = 1 {filtro}
            ORDER BY ventas.id DESC
            """,
            parametros,
        ).fetchall()


def exportar_csv(ruta_archivo, filas, columnas, encabezados):
    with open(ruta_archivo, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow([encabezados[columna] for columna in columnas])

        for fila in filas:
            escritor.writerow([fila[columna] for columna in columnas])


def abrir_reportes(ventana=None):
    ventana = ventana or tk.Toplevel()
    ventana.title("Reportes")
    ventana.geometry("980x620")

    frame = ttk.Frame(ventana, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(3, weight=1)

    fecha_inicio_var = tk.StringVar()
    fecha_fin_var = tk.StringVar()
    resumen_var = tk.StringVar()
    datos_reportes = {
        "bajo_stock": [],
        "mas_vendidos": [],
        "ventas": [],
    }

    filtros = ttk.Frame(frame)
    filtros.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    filtros.columnconfigure(1, weight=1)
    filtros.columnconfigure(3, weight=1)

    ttk.Label(filtros, text="Desde").grid(row=0, column=0, sticky=tk.W, padx=(0, 4))
    ttk.Entry(filtros, textvariable=fecha_inicio_var).grid(
        row=0,
        column=1,
        sticky="ew",
        padx=(0, 8),
    )
    ttk.Label(filtros, text="Hasta").grid(row=0, column=2, sticky=tk.W, padx=(0, 4))
    ttk.Entry(filtros, textvariable=fecha_fin_var).grid(
        row=0,
        column=3,
        sticky="ew",
        padx=(0, 8),
    )

    ttk.Label(frame, textvariable=resumen_var, justify=tk.LEFT).grid(
        row=1,
        column=0,
        sticky=tk.W,
        pady=(0, 8),
    )

    notebook = ttk.Notebook(frame)
    notebook.grid(row=3, column=0, sticky="nsew")

    bajo_stock_tab = ttk.Frame(notebook, padding=6)
    mas_vendidos_tab = ttk.Frame(notebook, padding=6)
    ventas_tab = ttk.Frame(notebook, padding=6)
    notebook.add(bajo_stock_tab, text="Bajo stock")
    notebook.add(mas_vendidos_tab, text="Mas vendidos")
    notebook.add(ventas_tab, text="Ventas")

    tabla_bajo_stock = _crear_tabla(
        bajo_stock_tab,
        ("id", "sku", "nombre", "stock_actual", "stock_minimo"),
        {
            "id": "ID",
            "sku": "SKU",
            "nombre": "Producto",
            "stock_actual": "Stock actual",
            "stock_minimo": "Stock minimo",
        },
    )

    tabla_mas_vendidos = _crear_tabla(
        mas_vendidos_tab,
        ("id", "sku", "nombre", "cantidad_vendida", "total_vendido"),
        {
            "id": "ID",
            "sku": "SKU",
            "nombre": "Producto",
            "cantidad_vendida": "Cantidad vendida",
            "total_vendido": "Total vendido",
        },
    )

    tabla_ventas = _crear_tabla(
        ventas_tab,
        ("id", "cliente", "total", "estado", "fecha"),
        {
            "id": "ID",
            "cliente": "Cliente",
            "total": "Total",
            "estado": "Estado",
            "fecha": "Fecha",
        },
    )

    def cargar_reportes():
        fecha_inicio = fecha_inicio_var.get().strip() or None
        fecha_fin = fecha_fin_var.get().strip() or None

        try:
            resumen = obtener_resumen_reportes(fecha_inicio, fecha_fin)
            productos_bajo_stock = obtener_productos_bajo_stock()
            productos_mas_vendidos = obtener_productos_mas_vendidos(
                fecha_inicio,
                fecha_fin,
            )
            ventas_recientes = obtener_ventas_recientes(fecha_inicio, fecha_fin)
        except Exception as error:
            messagebox.showerror("Reportes", str(error))
            return

        datos_reportes["bajo_stock"] = productos_bajo_stock
        datos_reportes["mas_vendidos"] = productos_mas_vendidos
        datos_reportes["ventas"] = ventas_recientes

        resumen_var.set(
            "Resumen general\n"
            f"Ventas completadas: {resumen['cantidad_ventas']}\n"
            f"Total ventas: L {resumen['total_ventas']:.2f}\n"
            f"Facturas emitidas: {resumen['cantidad_facturas']}\n"
            f"Total facturado: L {resumen['total_facturado']:.2f}\n"
            f"Productos bajo stock: {resumen['productos_bajo_stock']}"
        )

        _cargar_tabla(
            tabla_bajo_stock,
            productos_bajo_stock,
            ("id", "sku", "nombre", "stock_actual", "stock_minimo"),
        )
        _cargar_tabla(
            tabla_mas_vendidos,
            productos_mas_vendidos,
            ("id", "sku", "nombre", "cantidad_vendida", "total_vendido"),
            moneda={"total_vendido"},
        )
        _cargar_tabla(
            tabla_ventas,
            ventas_recientes,
            ("id", "cliente", "total", "estado", "fecha"),
            moneda={"total"},
        )

    def exportar_reporte_actual():
        indice_tab = notebook.index(notebook.select())
        configuraciones = [
            (
                "bajo_stock",
                "bajo_stock.csv",
                ("id", "sku", "nombre", "stock_actual", "stock_minimo"),
                {
                    "id": "ID",
                    "sku": "SKU",
                    "nombre": "Producto",
                    "stock_actual": "Stock actual",
                    "stock_minimo": "Stock minimo",
                },
            ),
            (
                "mas_vendidos",
                "mas_vendidos.csv",
                ("id", "sku", "nombre", "cantidad_vendida", "total_vendido"),
                {
                    "id": "ID",
                    "sku": "SKU",
                    "nombre": "Producto",
                    "cantidad_vendida": "Cantidad vendida",
                    "total_vendido": "Total vendido",
                },
            ),
            (
                "ventas",
                "ventas.csv",
                ("id", "cliente", "total", "estado", "fecha"),
                {
                    "id": "ID",
                    "cliente": "Cliente",
                    "total": "Total",
                    "estado": "Estado",
                    "fecha": "Fecha",
                },
            ),
        ]
        clave, archivo_sugerido, columnas, encabezados = configuraciones[indice_tab]

        if not datos_reportes[clave]:
            messagebox.showwarning("Reportes", "No hay datos para exportar.")
            return

        ruta_archivo = filedialog.asksaveasfilename(
            parent=ventana,
            title="Exportar reporte",
            defaultextension=".csv",
            initialfile=archivo_sugerido,
            filetypes=(("CSV", "*.csv"), ("Todos los archivos", "*.*")),
        )

        if not ruta_archivo:
            return

        try:
            exportar_csv(ruta_archivo, datos_reportes[clave], columnas, encabezados)
            messagebox.showinfo("Reportes", "Reporte exportado correctamente.")
        except Exception as error:
            messagebox.showerror("Reportes", str(error))

    acciones = ttk.Frame(frame)
    acciones.grid(row=2, column=0, sticky=tk.E, pady=(0, 8))

    ttk.Button(acciones, text="Exportar CSV", command=exportar_reporte_actual).pack(
        side=tk.LEFT,
        padx=(0, 6),
    )
    ttk.Button(acciones, text="Actualizar reportes", command=cargar_reportes).pack(
        side=tk.LEFT,
    )

    cargar_reportes()


def _crear_tabla(contenedor, columnas, encabezados):
    contenedor.columnconfigure(0, weight=1)
    contenedor.rowconfigure(0, weight=1)

    tabla = ttk.Treeview(contenedor, columns=columnas, show="headings")

    for columna in columnas:
        tabla.heading(columna, text=encabezados[columna])
        tabla.column(columna, width=140, anchor=tk.W)

    scroll = ttk.Scrollbar(contenedor, orient=tk.VERTICAL, command=tabla.yview)
    tabla.configure(yscrollcommand=scroll.set)
    tabla.grid(row=0, column=0, sticky="nsew")
    scroll.grid(row=0, column=1, sticky="ns")

    return tabla


def _cargar_tabla(tabla, filas, columnas, moneda=None):
    moneda = moneda or set()

    for item in tabla.get_children():
        tabla.delete(item)

    for fila in filas:
        valores = []
        for columna in columnas:
            valor = fila[columna]
            if columna in moneda:
                valor = f"L {float(valor):.2f}"
            valores.append(valor)

        tabla.insert("", tk.END, values=tuple(valores))


def _crear_filtro_fechas(campo_fecha, fecha_inicio=None, fecha_fin=None):
    filtros = []
    parametros = []

    if fecha_inicio:
        filtros.append(f"AND date({campo_fecha}) >= date(?)")
        parametros.append(fecha_inicio)

    if fecha_fin:
        filtros.append(f"AND date({campo_fecha}) <= date(?)")
        parametros.append(fecha_fin)

    return " ".join(filtros), parametros
