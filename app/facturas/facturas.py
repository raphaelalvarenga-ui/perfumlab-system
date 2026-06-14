import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from app.database.conexion import inicializar_base_datos, obtener_conexion


def crear_tabla_facturas():
    inicializar_base_datos()


def generar_factura(venta_id):
    inicializar_base_datos()

    with obtener_conexion() as conexion:
        venta = conexion.execute(
            "SELECT id, total, estado FROM ventas WHERE id = ?",
            (venta_id,),
        ).fetchone()

        if venta is None:
            return False, "La venta no existe."

        if venta["estado"] != "Completada":
            return False, "Solo se pueden facturar ventas completadas."

        factura = conexion.execute(
            "SELECT numero_factura FROM facturas WHERE venta_id = ?",
            (venta_id,),
        ).fetchone()

        if factura:
            return False, f"La venta ya tiene factura: {factura['numero_factura']}."

        numero_factura = f"FAC-{int(venta_id):06d}"
        conexion.execute(
            """
            INSERT INTO facturas (venta_id, numero_factura, total)
            VALUES (?, ?, ?)
            """,
            (venta_id, numero_factura, venta["total"]),
        )

    return True, f"Factura {numero_factura} generada correctamente."


def obtener_facturas():
    inicializar_base_datos()

    with obtener_conexion() as conexion:
        return conexion.execute(
            """
            SELECT
                facturas.id,
                facturas.numero_factura,
                facturas.venta_id,
                clientes.nombre AS cliente,
                facturas.total,
                facturas.fecha
            FROM facturas
            INNER JOIN ventas ON ventas.id = facturas.venta_id
            LEFT JOIN clientes ON clientes.id = ventas.cliente_id
            ORDER BY facturas.id DESC
            """
        ).fetchall()


def obtener_factura_por_id(factura_id):
    inicializar_base_datos()

    with obtener_conexion() as conexion:
        return conexion.execute(
            """
            SELECT
                facturas.id,
                facturas.numero_factura,
                facturas.venta_id,
                clientes.nombre AS cliente,
                facturas.total,
                facturas.fecha
            FROM facturas
            INNER JOIN ventas ON ventas.id = facturas.venta_id
            LEFT JOIN clientes ON clientes.id = ventas.cliente_id
            WHERE facturas.id = ?
            """,
            (factura_id,),
        ).fetchone()


def obtener_detalle_factura(factura_id):
    inicializar_base_datos()

    with obtener_conexion() as conexion:
        return conexion.execute(
            """
            SELECT
                productos.nombre AS producto,
                detalle_venta.cantidad,
                detalle_venta.precio_unitario,
                detalle_venta.subtotal
            FROM facturas
            INNER JOIN detalle_venta ON detalle_venta.venta_id = facturas.venta_id
            INNER JOIN productos ON productos.id = detalle_venta.producto_id
            WHERE facturas.id = ?
            ORDER BY detalle_venta.id ASC
            """,
            (factura_id,),
        ).fetchall()


def obtener_ventas_para_facturar():
    inicializar_base_datos()

    with obtener_conexion() as conexion:
        return conexion.execute(
            """
            SELECT
                ventas.id,
                clientes.nombre AS cliente,
                ventas.total,
                ventas.fecha
            FROM ventas
            LEFT JOIN clientes ON clientes.id = ventas.cliente_id
            LEFT JOIN facturas ON facturas.venta_id = ventas.id
            WHERE facturas.id IS NULL AND ventas.estado = 'Completada'
            ORDER BY ventas.id DESC
            """
        ).fetchall()


def generar_texto_factura(factura_id):
    factura = obtener_factura_por_id(factura_id)
    if factura is None:
        raise ValueError("La factura no existe.")

    detalles = obtener_detalle_factura(factura_id)
    cliente = factura["cliente"] or "Sin cliente"
    lineas = [
        "PERFUM LAB",
        "FACTURA",
        "=" * 48,
        f"Factura: {factura['numero_factura']}",
        f"Venta: #{factura['venta_id']}",
        f"Cliente: {cliente}",
        f"Fecha: {factura['fecha']}",
        "-" * 48,
        f"{'Producto':24} {'Cant.':>5} {'Precio':>8} {'Subtotal':>9}",
        "-" * 48,
    ]

    for detalle in detalles:
        producto = detalle["producto"][:24]
        lineas.append(
            f"{producto:24} "
            f"{detalle['cantidad']:>5} "
            f"{detalle['precio_unitario']:>8.2f} "
            f"{detalle['subtotal']:>9.2f}"
        )

    lineas.extend(
        [
            "-" * 48,
            f"{'TOTAL':>39} L {factura['total']:.2f}",
            "=" * 48,
        ]
    )

    return "\n".join(lineas)


def exportar_factura_txt(factura_id, ruta_archivo):
    texto = generar_texto_factura(factura_id)

    with open(ruta_archivo, "w", encoding="utf-8") as archivo:
        archivo.write(texto)


def abrir_facturas(ventana=None):
    ventana = ventana or tk.Toplevel()
    ventana.title("Facturas")
    ventana.geometry("980x620")

    frame = ttk.Frame(ventana, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(2, weight=1)

    venta_var = tk.StringVar()
    resumen_var = tk.StringVar(value="Seleccione una factura para ver su detalle.")
    ventas_cache = {}

    formulario = ttk.Frame(frame)
    formulario.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    formulario.columnconfigure(1, weight=1)

    ttk.Label(formulario, text="Venta pendiente").grid(row=0, column=0, sticky=tk.W)
    venta_combo = ttk.Combobox(formulario, textvariable=venta_var, state="readonly")
    venta_combo.grid(row=0, column=1, sticky="ew", padx=6)

    botones = ttk.Frame(frame)
    botones.grid(row=1, column=0, sticky="ew", pady=(0, 8))

    panel = ttk.PanedWindow(frame, orient=tk.VERTICAL)
    panel.grid(row=2, column=0, sticky="nsew")

    facturas_frame = ttk.LabelFrame(panel, text="Facturas emitidas")
    detalle_frame = ttk.LabelFrame(panel, text="Detalle de factura")
    panel.add(facturas_frame, weight=2)
    panel.add(detalle_frame, weight=2)

    facturas_frame.columnconfigure(0, weight=1)
    facturas_frame.rowconfigure(0, weight=1)
    detalle_frame.columnconfigure(0, weight=1)
    detalle_frame.rowconfigure(1, weight=1)

    columnas_facturas = ("id", "numero_factura", "venta_id", "cliente", "total", "fecha")
    tabla_facturas = ttk.Treeview(facturas_frame, columns=columnas_facturas, show="headings")
    encabezados_facturas = {
        "id": "ID",
        "numero_factura": "Factura",
        "venta_id": "Venta",
        "cliente": "Cliente",
        "total": "Total",
        "fecha": "Fecha",
    }

    for columna in columnas_facturas:
        tabla_facturas.heading(columna, text=encabezados_facturas[columna])
        tabla_facturas.column(columna, width=130, anchor=tk.W)

    scroll_facturas = ttk.Scrollbar(
        facturas_frame,
        orient=tk.VERTICAL,
        command=tabla_facturas.yview,
    )
    tabla_facturas.configure(yscrollcommand=scroll_facturas.set)
    tabla_facturas.grid(row=0, column=0, sticky="nsew")
    scroll_facturas.grid(row=0, column=1, sticky="ns")

    ttk.Label(detalle_frame, textvariable=resumen_var).grid(
        row=0,
        column=0,
        sticky=tk.W,
        pady=(0, 6),
    )

    columnas_detalle = ("producto", "cantidad", "precio_unitario", "subtotal")
    tabla_detalle = ttk.Treeview(detalle_frame, columns=columnas_detalle, show="headings")
    encabezados_detalle = {
        "producto": "Producto",
        "cantidad": "Cantidad",
        "precio_unitario": "Precio unitario",
        "subtotal": "Subtotal",
    }

    for columna in columnas_detalle:
        tabla_detalle.heading(columna, text=encabezados_detalle[columna])
        tabla_detalle.column(columna, width=160, anchor=tk.W)

    scroll_detalle = ttk.Scrollbar(
        detalle_frame,
        orient=tk.VERTICAL,
        command=tabla_detalle.yview,
    )
    tabla_detalle.configure(yscrollcommand=scroll_detalle.set)
    tabla_detalle.grid(row=1, column=0, sticky="nsew")
    scroll_detalle.grid(row=1, column=1, sticky="ns")

    def cargar_ventas_pendientes():
        ventas_cache.clear()
        opciones = []

        for venta in obtener_ventas_para_facturar():
            cliente = venta["cliente"] or "Sin cliente"
            etiqueta = f"{venta['id']} - {cliente} - L {venta['total']:.2f}"
            ventas_cache[etiqueta] = venta["id"]
            opciones.append(etiqueta)

        venta_combo["values"] = opciones
        venta_var.set(opciones[0] if opciones else "")

    def cargar_facturas():
        for item in tabla_facturas.get_children():
            tabla_facturas.delete(item)

        for factura in obtener_facturas():
            tabla_facturas.insert(
                "",
                tk.END,
                iid=str(factura["id"]),
                values=(
                    factura["id"],
                    factura["numero_factura"],
                    factura["venta_id"],
                    factura["cliente"],
                    f"L {factura['total']:.2f}",
                    factura["fecha"],
                ),
            )

    def cargar_detalle_factura(factura_id):
        for item in tabla_detalle.get_children():
            tabla_detalle.delete(item)

        factura = obtener_factura_por_id(factura_id)
        if factura is None:
            resumen_var.set("Seleccione una factura para ver su detalle.")
            return

        cliente = factura["cliente"] or "Sin cliente"
        resumen_var.set(
            f"{factura['numero_factura']} | Venta #{factura['venta_id']} | "
            f"Cliente: {cliente} | Total: L {factura['total']:.2f}"
        )

        for detalle in obtener_detalle_factura(factura_id):
            tabla_detalle.insert(
                "",
                tk.END,
                values=(
                    detalle["producto"],
                    detalle["cantidad"],
                    f"L {detalle['precio_unitario']:.2f}",
                    f"L {detalle['subtotal']:.2f}",
                ),
            )

    def al_seleccionar_factura(_evento=None):
        seleccion = tabla_facturas.selection()
        if not seleccion:
            return

        cargar_detalle_factura(int(seleccion[0]))

    def guardar_factura():
        venta_id = ventas_cache.get(venta_var.get())
        if venta_id is None:
            messagebox.showwarning("Facturas", "Seleccione una venta pendiente.")
            return

        ok, mensaje = generar_factura(venta_id)

        if ok:
            messagebox.showinfo("Facturas", mensaje)
            cargar_ventas_pendientes()
            cargar_facturas()
        else:
            messagebox.showerror("Facturas", mensaje)

    def exportar_factura_seleccionada():
        seleccion = tabla_facturas.selection()
        if not seleccion:
            messagebox.showwarning("Facturas", "Seleccione una factura.")
            return

        factura_id = int(seleccion[0])
        factura = obtener_factura_por_id(factura_id)
        if factura is None:
            messagebox.showerror("Facturas", "La factura seleccionada no existe.")
            return

        ruta_archivo = filedialog.asksaveasfilename(
            parent=ventana,
            title="Exportar factura",
            defaultextension=".txt",
            initialfile=f"{factura['numero_factura']}.txt",
            filetypes=(("Texto", "*.txt"), ("Todos los archivos", "*.*")),
        )

        if not ruta_archivo:
            return

        try:
            exportar_factura_txt(factura_id, ruta_archivo)
            messagebox.showinfo("Facturas", "Factura exportada correctamente.")
        except Exception as error:
            messagebox.showerror("Facturas", str(error))

    def actualizar_todo():
        cargar_ventas_pendientes()
        cargar_facturas()

    tabla_facturas.bind("<<TreeviewSelect>>", al_seleccionar_factura)

    ttk.Button(botones, text="Generar factura", command=guardar_factura).pack(
        side=tk.LEFT,
        padx=(0, 6),
    )
    ttk.Button(botones, text="Ver detalle", command=al_seleccionar_factura).pack(
        side=tk.LEFT,
        padx=(0, 6),
    )
    ttk.Button(botones, text="Exportar factura", command=exportar_factura_seleccionada).pack(
        side=tk.LEFT,
        padx=(0, 6),
    )
    ttk.Button(botones, text="Actualizar", command=actualizar_todo).pack(side=tk.LEFT)

    cargar_ventas_pendientes()
    cargar_facturas()
