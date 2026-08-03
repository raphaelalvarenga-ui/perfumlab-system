import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from app.database.json_storage import (
    DATABASE_PATH,
    buscar_por_id,
    cargar_todo,
    es_activo,
    inicializar_datos_json,
)
from app.ui_theme import aplicar_tema, configurar_tabla, crear_encabezado
from app.validaciones import (
    validar_fecha_iso,
    validar_rango_fechas,
    validar_ruta_exportacion,
)


def obtener_resumen_reportes(fecha_inicio=None, fecha_fin=None, ruta_db=DATABASE_PATH):
    inicializar_datos_json(ruta_db)
    fecha_inicio, fecha_fin = validar_rango_fechas(fecha_inicio, fecha_fin)
    datos = cargar_todo(ruta_db)
    ventas_completadas = [
        venta
        for venta in datos["ventas"]
        if venta["estado"] == "Completada"
        and _fecha_en_rango(venta["fecha"], fecha_inicio, fecha_fin)
    ]
    venta_ids = {int(venta["id"]) for venta in ventas_completadas}
    facturas = [
        factura
        for factura in datos["facturas"]
        if int(factura["venta_id"]) in venta_ids
    ]
    productos_bajo_stock = [
        producto
        for producto in datos["productos"]
        if es_activo(producto)
        and int(producto["stock_actual"]) <= int(producto["stock_minimo"])
    ]

    return {
        "cantidad_ventas": len(ventas_completadas),
        "total_ventas": sum(float(venta["total"]) for venta in ventas_completadas),
        "cantidad_facturas": len(facturas),
        "total_facturado": sum(float(factura["total"]) for factura in facturas),
        "productos_bajo_stock": len(productos_bajo_stock),
    }


def obtener_productos_bajo_stock(ruta_db=DATABASE_PATH):
    datos = cargar_todo(ruta_db)
    productos = [
        {
            "id": producto["id"],
            "sku": producto["sku"],
            "nombre": producto["nombre"],
            "stock_actual": int(producto["stock_actual"]),
            "stock_minimo": int(producto["stock_minimo"]),
        }
        for producto in datos["productos"]
        if es_activo(producto)
        and int(producto["stock_actual"]) <= int(producto["stock_minimo"])
    ]
    productos.sort(key=lambda producto: (producto["stock_actual"], producto["nombre"].lower()))
    return productos


def obtener_productos_mas_vendidos(
    fecha_inicio=None,
    fecha_fin=None,
    ruta_db=DATABASE_PATH,
):
    fecha_inicio, fecha_fin = validar_rango_fechas(fecha_inicio, fecha_fin)
    datos = cargar_todo(ruta_db)
    ventas_validas = {
        int(venta["id"])
        for venta in datos["ventas"]
        if venta["estado"] == "Completada"
        and _fecha_en_rango(venta["fecha"], fecha_inicio, fecha_fin)
    }
    resumen = {}

    for detalle in datos["detalle_venta"]:
        if int(detalle["venta_id"]) not in ventas_validas:
            continue

        producto = buscar_por_id(datos["productos"], detalle["producto_id"])
        if producto is None:
            continue

        producto_id = int(producto["id"])
        if producto_id not in resumen:
            resumen[producto_id] = {
                "id": producto["id"],
                "sku": producto["sku"],
                "nombre": producto["nombre"],
                "cantidad_vendida": 0,
                "total_vendido": 0.0,
            }

        resumen[producto_id]["cantidad_vendida"] += int(detalle["cantidad"])
        resumen[producto_id]["total_vendido"] += float(detalle["subtotal"])

    productos = list(resumen.values())
    productos.sort(
        key=lambda producto: (
            producto["cantidad_vendida"],
            producto["total_vendido"],
        ),
        reverse=True,
    )
    return productos


def obtener_ventas_recientes(fecha_inicio=None, fecha_fin=None, ruta_db=DATABASE_PATH):
    fecha_inicio, fecha_fin = validar_rango_fechas(fecha_inicio, fecha_fin)
    datos = cargar_todo(ruta_db)
    ventas = [
        {
            "id": venta["id"],
            "cliente": _nombre_cliente(datos["clientes"], venta.get("cliente_id")),
            "total": float(venta["total"]),
            "estado": venta["estado"],
            "fecha": venta["fecha"],
        }
        for venta in datos["ventas"]
        if _fecha_en_rango(venta["fecha"], fecha_inicio, fecha_fin)
    ]
    ventas.sort(key=lambda venta: int(venta["id"]), reverse=True)
    return ventas


def exportar_csv(ruta_archivo, filas, columnas, encabezados):
    ruta_archivo = validar_ruta_exportacion(
        ruta_archivo,
        ".csv",
        "el reporte CSV",
    )
    _validar_estructura_csv(filas, columnas, encabezados)

    with open(ruta_archivo, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow([encabezados[columna] for columna in columnas])

        for fila in filas:
            escritor.writerow([fila[columna] for columna in columnas])


def abrir_reportes(ventana=None):
    standalone = ventana is None
    contenedor = ventana or tk.Tk()
    raiz = contenedor.winfo_toplevel()
    aplicar_tema(raiz)
    raiz.title("Perfum Lab - Reportes")
    raiz.geometry("1180x720")
    raiz.minsize(980, 620)

    frame = ttk.Frame(contenedor, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(4, weight=1)

    fecha_inicio_var = tk.StringVar()
    fecha_fin_var = tk.StringVar()
    resumen_var = tk.StringVar()
    datos_reportes = {
        "bajo_stock": [],
        "mas_vendidos": [],
        "ventas": [],
    }

    crear_encabezado(
        frame,
        "Reportes",
        "Consulta ventas, facturacion, productos destacados y bajo stock.",
    )

    filtros = ttk.Frame(frame, style="Toolbar.TFrame", padding=(12, 10))
    filtros.grid(row=1, column=0, sticky="ew", pady=(0, 8))
    filtros.columnconfigure(1, weight=1)
    filtros.columnconfigure(3, weight=1)

    ttk.Label(
        filtros,
        text="Desde",
        style="Toolbar.TLabel",
    ).grid(row=0, column=0, sticky=tk.W, padx=(0, 4))
    ttk.Entry(filtros, textvariable=fecha_inicio_var).grid(
        row=0,
        column=1,
        sticky="ew",
        padx=(0, 8),
    )
    ttk.Label(
        filtros,
        text="Hasta",
        style="Toolbar.TLabel",
    ).grid(row=0, column=2, sticky=tk.W, padx=(0, 4))
    ttk.Entry(filtros, textvariable=fecha_fin_var).grid(
        row=0,
        column=3,
        sticky="ew",
        padx=(0, 8),
    )

    ttk.Label(frame, textvariable=resumen_var, justify=tk.LEFT).grid(
        row=2,
        column=0,
        sticky=tk.W,
        pady=(0, 8),
    )

    notebook = ttk.Notebook(frame)
    notebook.grid(row=4, column=0, sticky="nsew")

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
            parent=raiz,
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
    acciones.grid(row=3, column=0, sticky="ew", pady=(0, 8))
    acciones.columnconfigure(1, weight=1)

    ttk.Button(
        acciones,
        text="Exportar CSV",
        command=exportar_reporte_actual,
        style="Accent.TButton",
    ).grid(row=0, column=0, sticky=tk.W)
    ttk.Button(
        acciones,
        text="Actualizar reportes",
        command=cargar_reportes,
        style="Primary.TButton",
    ).grid(row=0, column=2, sticky=tk.E)

    cargar_reportes()

    if standalone:
        raiz.mainloop()


def _crear_tabla(contenedor, columnas, encabezados):
    contenedor.columnconfigure(0, weight=1)
    contenedor.rowconfigure(0, weight=1)

    tabla = ttk.Treeview(contenedor, columns=columnas, show="headings")

    for columna in columnas:
        tabla.heading(columna, text=encabezados[columna])
        tabla.column(columna, width=140, anchor=tk.W)

    configurar_tabla(tabla)
    scroll = ttk.Scrollbar(contenedor, orient=tk.VERTICAL, command=tabla.yview)
    tabla.configure(yscrollcommand=scroll.set)
    tabla.grid(row=0, column=0, sticky="nsew")
    scroll.grid(row=0, column=1, sticky="ns")

    return tabla


def _cargar_tabla(tabla, filas, columnas, moneda=None):
    moneda = moneda or set()

    for item in tabla.get_children():
        tabla.delete(item)

    for indice, fila in enumerate(filas):
        valores = []
        for columna in columnas:
            valor = fila[columna]
            if columna in moneda:
                valor = f"L {float(valor):.2f}"
            valores.append(valor)

        tabla.insert(
            "",
            tk.END,
            tags=("even" if indice % 2 else "odd",),
            values=tuple(valores),
        )


def _fecha_en_rango(fecha, fecha_inicio=None, fecha_fin=None):
    fecha = validar_fecha_iso(str(fecha or "")[:10], "fecha del registro")

    if fecha_inicio and fecha < fecha_inicio:
        return False

    if fecha_fin and fecha > fecha_fin:
        return False

    return True


def _validar_estructura_csv(filas, columnas, encabezados):
    if not columnas:
        raise ValueError("Debe indicar al menos una columna para exportar.")

    columnas_faltantes = [columna for columna in columnas if columna not in encabezados]
    if columnas_faltantes:
        raise ValueError(
            "Faltan encabezados para estas columnas: "
            + ", ".join(columnas_faltantes)
        )

    for indice, fila in enumerate(filas, start=1):
        faltantes = [columna for columna in columnas if columna not in fila]
        if faltantes:
            raise ValueError(
                f"La fila {indice} no contiene estas columnas: "
                + ", ".join(faltantes)
            )


def _nombre_cliente(clientes, cliente_id):
    if cliente_id is None:
        return None

    cliente = buscar_por_id(clientes, cliente_id)
    return cliente["nombre"] if cliente else None
