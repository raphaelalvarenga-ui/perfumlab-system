import tkinter as tk
from tkinter import messagebox, ttk

from app.database.conexion import inicializar_base_datos, obtener_conexion
from app.ui_theme import aplicar_tema, configurar_tabla, crear_encabezado


def crear_tabla_ventas():
    inicializar_base_datos()


def obtener_productos_para_venta():
    inicializar_base_datos()

    with obtener_conexion() as conexion:
        return conexion.execute(
            """
            SELECT id, sku, nombre, precio, stock_actual
            FROM productos
            WHERE activo = 1
            ORDER BY nombre ASC
            """
        ).fetchall()


def registrar_venta(producto_id, cliente, cantidad, usuario_id=1):
    return registrar_venta_multiple(
        cliente,
        [{"producto_id": producto_id, "cantidad": cantidad}],
        usuario_id=usuario_id,
    )


def registrar_venta_multiple(cliente, items, usuario_id=1):
    inicializar_base_datos()

    if not cliente.strip():
        return False, "El nombre del cliente es obligatorio."

    try:
        items_normalizados = _normalizar_items(items)
    except ValueError as error:
        return False, str(error)

    if not items_normalizados:
        return False, "Debe agregar al menos un producto a la venta."

    with obtener_conexion() as conexion:
        productos = _obtener_productos_por_id(
            conexion,
            [item["producto_id"] for item in items_normalizados],
        )

        total = 0
        detalles = []

        for item in items_normalizados:
            producto = productos.get(item["producto_id"])

            if producto is None:
                return False, f"El producto {item['producto_id']} no existe o esta inactivo."

            cantidad = item["cantidad"]
            stock_actual = int(producto["stock_actual"])

            if cantidad > stock_actual:
                return (
                    False,
                    f"No hay suficiente stock para {producto['nombre']}. "
                    f"Disponible: {stock_actual}.",
                )

            precio = float(producto["precio"])
            subtotal = precio * cantidad
            total += subtotal
            detalles.append(
                {
                    "producto": producto,
                    "cantidad": cantidad,
                    "precio": precio,
                    "subtotal": subtotal,
                    "stock_anterior": stock_actual,
                    "stock_nuevo": stock_actual - cantidad,
                }
            )

        cliente_id = _obtener_o_crear_cliente(conexion, cliente)
        cursor = conexion.execute(
            """
            INSERT INTO ventas (cliente_id, usuario_id, total, estado)
            VALUES (?, ?, ?, ?)
            """,
            (cliente_id, usuario_id, total, "Completada"),
        )
        venta_id = cursor.lastrowid

        for detalle in detalles:
            producto = detalle["producto"]

            conexion.execute(
                """
                INSERT INTO detalle_venta (
                    venta_id,
                    producto_id,
                    cantidad,
                    precio_unitario,
                    subtotal
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    venta_id,
                    producto["id"],
                    detalle["cantidad"],
                    detalle["precio"],
                    detalle["subtotal"],
                ),
            )

            conexion.execute(
                """
                UPDATE productos
                SET stock_actual = ?, fecha_actualizacion = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (detalle["stock_nuevo"], producto["id"]),
            )

            conexion.execute(
                """
                INSERT INTO movimientos_inventario (
                    producto_id,
                    tipo_movimiento,
                    cantidad,
                    stock_anterior,
                    stock_nuevo,
                    motivo
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    producto["id"],
                    "SALIDA",
                    detalle["cantidad"],
                    detalle["stock_anterior"],
                    detalle["stock_nuevo"],
                    f"Venta #{venta_id} - {cliente.strip()}",
                ),
            )

    return True, f"Venta #{venta_id} registrada correctamente. Total: L {total:.2f}"


def anular_venta(venta_id):
    inicializar_base_datos()

    with obtener_conexion() as conexion:
        venta = conexion.execute(
            "SELECT id, estado FROM ventas WHERE id = ?",
            (venta_id,),
        ).fetchone()

        if venta is None:
            return False, "La venta no existe."

        if venta["estado"] == "Anulada":
            return False, "La venta ya esta anulada."

        factura = conexion.execute(
            "SELECT id FROM facturas WHERE venta_id = ?",
            (venta_id,),
        ).fetchone()

        if factura is not None:
            return False, "No se puede anular una venta que ya tiene factura."

        detalles = conexion.execute(
            """
            SELECT
                detalle_venta.producto_id,
                productos.nombre,
                productos.stock_actual,
                detalle_venta.cantidad
            FROM detalle_venta
            INNER JOIN productos ON productos.id = detalle_venta.producto_id
            WHERE detalle_venta.venta_id = ?
            """,
            (venta_id,),
        ).fetchall()

        if not detalles:
            return False, "La venta no tiene detalle de productos."

        for detalle in detalles:
            stock_anterior = int(detalle["stock_actual"])
            cantidad = int(detalle["cantidad"])
            stock_nuevo = stock_anterior + cantidad

            conexion.execute(
                """
                UPDATE productos
                SET stock_actual = ?, fecha_actualizacion = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (stock_nuevo, detalle["producto_id"]),
            )

            conexion.execute(
                """
                INSERT INTO movimientos_inventario (
                    producto_id,
                    tipo_movimiento,
                    cantidad,
                    stock_anterior,
                    stock_nuevo,
                    motivo
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    detalle["producto_id"],
                    "ENTRADA",
                    cantidad,
                    stock_anterior,
                    stock_nuevo,
                    f"Anulacion de venta #{venta_id}",
                ),
            )

        conexion.execute(
            "UPDATE ventas SET estado = ? WHERE id = ?",
            ("Anulada", venta_id),
        )

    return True, f"Venta #{venta_id} anulada correctamente. Stock devuelto."


def obtener_ventas():
    inicializar_base_datos()

    with obtener_conexion() as conexion:
        return conexion.execute(
            """
            SELECT
                ventas.id,
                GROUP_CONCAT(
                    productos.nombre || ' x' || detalle_venta.cantidad,
                    ', '
                ) AS producto,
                clientes.nombre AS cliente,
                SUM(detalle_venta.cantidad) AS cantidad,
                NULL AS precio_unitario,
                ventas.total AS total,
                ventas.estado,
                ventas.fecha
            FROM ventas
            INNER JOIN detalle_venta ON detalle_venta.venta_id = ventas.id
            INNER JOIN productos ON productos.id = detalle_venta.producto_id
            LEFT JOIN clientes ON clientes.id = ventas.cliente_id
            GROUP BY ventas.id, clientes.nombre, ventas.total, ventas.estado, ventas.fecha
            ORDER BY ventas.id DESC
            """
        ).fetchall()


def obtener_detalle_venta(venta_id):
    inicializar_base_datos()

    with obtener_conexion() as conexion:
        return conexion.execute(
            """
            SELECT
                detalle_venta.id,
                detalle_venta.venta_id,
                productos.nombre AS producto,
                detalle_venta.cantidad,
                detalle_venta.precio_unitario,
                detalle_venta.subtotal
            FROM detalle_venta
            INNER JOIN productos ON productos.id = detalle_venta.producto_id
            WHERE detalle_venta.venta_id = ?
            ORDER BY detalle_venta.id ASC
            """,
            (venta_id,),
        ).fetchall()


def buscar_venta_por_id(venta_id):
    inicializar_base_datos()

    with obtener_conexion() as conexion:
        return conexion.execute(
            """
            SELECT
                ventas.id,
                GROUP_CONCAT(
                    productos.nombre || ' x' || detalle_venta.cantidad,
                    ', '
                ) AS producto,
                clientes.nombre AS cliente,
                SUM(detalle_venta.cantidad) AS cantidad,
                NULL AS precio_unitario,
                ventas.total AS total,
                ventas.estado,
                ventas.fecha
            FROM ventas
            INNER JOIN detalle_venta ON detalle_venta.venta_id = ventas.id
            INNER JOIN productos ON productos.id = detalle_venta.producto_id
            LEFT JOIN clientes ON clientes.id = ventas.cliente_id
            WHERE ventas.id = ?
            GROUP BY ventas.id, clientes.nombre, ventas.total, ventas.estado, ventas.fecha
            """,
            (venta_id,),
        ).fetchone()


def abrir_ventas(ventana=None):
    standalone = ventana is None
    contenedor = ventana or tk.Tk()
    raiz = contenedor.winfo_toplevel()
    aplicar_tema(raiz)
    raiz.title("Perfum Lab - Ventas")
    raiz.geometry("1180x720")
    raiz.minsize(980, 620)

    frame = ttk.Frame(contenedor, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(4, weight=1)

    producto_var = tk.StringVar()
    cliente_var = tk.StringVar()
    cantidad_var = tk.StringVar(value="1")
    total_var = tk.StringVar(value="Total carrito: L 0.00")
    productos_cache = {}
    carrito = []

    crear_encabezado(
        frame,
        "Ventas",
        "Arma el carrito, valida stock y registra ventas completadas.",
    )

    formulario = ttk.Frame(frame, style="Toolbar.TFrame", padding=(12, 10))
    formulario.grid(row=1, column=0, sticky="ew", pady=(0, 10))
    formulario.columnconfigure(1, weight=1)
    formulario.columnconfigure(3, weight=1)

    ttk.Label(
        formulario,
        text="Producto",
        style="Toolbar.TLabel",
    ).grid(row=0, column=0, sticky=tk.W, padx=4)
    producto_combo = ttk.Combobox(formulario, textvariable=producto_var, state="readonly")
    producto_combo.grid(row=0, column=1, sticky="ew", padx=4)

    ttk.Label(
        formulario,
        text="Cliente",
        style="Toolbar.TLabel",
    ).grid(row=0, column=2, sticky=tk.W, padx=4)
    ttk.Entry(formulario, textvariable=cliente_var).grid(
        row=0,
        column=3,
        sticky="ew",
        padx=4,
    )

    ttk.Label(
        formulario,
        text="Cantidad",
        style="Toolbar.TLabel",
    ).grid(row=0, column=4, sticky=tk.W, padx=4)
    ttk.Entry(formulario, textvariable=cantidad_var, width=8).grid(
        row=0,
        column=5,
        sticky=tk.W,
        padx=4,
    )

    carrito_frame = ttk.LabelFrame(frame, text="Carrito")
    carrito_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
    carrito_frame.columnconfigure(0, weight=1)
    carrito_frame.rowconfigure(0, weight=1)

    columnas_carrito = ("producto", "cantidad", "precio_unitario", "subtotal")
    tabla_carrito = ttk.Treeview(carrito_frame, columns=columnas_carrito, show="headings", height=6)
    encabezados_carrito = {
        "producto": "Producto",
        "cantidad": "Cantidad",
        "precio_unitario": "Precio unitario",
        "subtotal": "Subtotal",
    }

    for columna in columnas_carrito:
        tabla_carrito.heading(columna, text=encabezados_carrito[columna])
        tabla_carrito.column(columna, width=150, anchor=tk.W)

    configurar_tabla(tabla_carrito)
    tabla_carrito.grid(row=0, column=0, sticky="nsew")

    botones_carrito = ttk.Frame(frame)
    botones_carrito.grid(row=3, column=0, sticky="ew", pady=(0, 8))
    botones_carrito.columnconfigure(1, weight=1)

    acciones_carrito = ttk.Frame(botones_carrito)
    acciones_carrito.grid(row=0, column=0, sticky=tk.W)
    resumen_carrito = ttk.Label(
        botones_carrito,
        textvariable=total_var,
        style="Section.TLabel",
    )
    resumen_carrito.grid(row=0, column=1, sticky=tk.E, padx=12)
    acciones_venta = ttk.Frame(botones_carrito)
    acciones_venta.grid(row=0, column=2, sticky=tk.E)

    ventas_frame = ttk.LabelFrame(frame, text="Ventas registradas")
    ventas_frame.grid(row=4, column=0, sticky="nsew")
    ventas_frame.columnconfigure(0, weight=1)
    ventas_frame.rowconfigure(0, weight=1)

    columnas_ventas = (
        "id",
        "producto",
        "cliente",
        "cantidad",
        "precio_unitario",
        "total",
        "estado",
        "fecha",
    )
    tabla_ventas = ttk.Treeview(ventas_frame, columns=columnas_ventas, show="headings")
    encabezados_ventas = {
        "id": "ID",
        "producto": "Productos",
        "cliente": "Cliente",
        "cantidad": "Cantidad total",
        "precio_unitario": "Precio unitario",
        "total": "Total",
        "estado": "Estado",
        "fecha": "Fecha",
    }

    for columna in columnas_ventas:
        tabla_ventas.heading(columna, text=encabezados_ventas[columna])
        tabla_ventas.column(columna, width=120, anchor=tk.W)

    configurar_tabla(tabla_ventas)
    scroll = ttk.Scrollbar(ventas_frame, orient=tk.VERTICAL, command=tabla_ventas.yview)
    tabla_ventas.configure(yscrollcommand=scroll.set)
    tabla_ventas.grid(row=0, column=0, sticky="nsew")
    scroll.grid(row=0, column=1, sticky="ns")

    def cargar_productos():
        productos_cache.clear()
        opciones = []

        for producto in obtener_productos_para_venta():
            etiqueta = (
                f"{producto['id']} - {producto['nombre']} "
                f"(Stock: {producto['stock_actual']}, L {producto['precio']:.2f})"
            )
            productos_cache[etiqueta] = {
                "id": producto["id"],
                "nombre": producto["nombre"],
                "precio": float(producto["precio"]),
                "stock_actual": int(producto["stock_actual"]),
            }
            opciones.append(etiqueta)

        producto_combo["values"] = opciones
        producto_var.set(opciones[0] if opciones else "")

    def cargar_ventas():
        for item in tabla_ventas.get_children():
            tabla_ventas.delete(item)

        for indice, venta in enumerate(obtener_ventas()):
            tabla_ventas.insert(
                "",
                tk.END,
                tags=("even" if indice % 2 else "odd",),
                values=(
                    venta["id"],
                    venta["producto"],
                    venta["cliente"],
                    venta["cantidad"],
                    "",
                    f"L {venta['total']:.2f}",
                    venta["estado"],
                    venta["fecha"],
                ),
            )

    def refrescar_carrito():
        for item in tabla_carrito.get_children():
            tabla_carrito.delete(item)

        total = 0
        for indice, item in enumerate(carrito):
            total += item["subtotal"]
            tabla_carrito.insert(
                "",
                tk.END,
                iid=str(item["producto_id"]),
                tags=("even" if indice % 2 else "odd",),
                values=(
                    item["nombre"],
                    item["cantidad"],
                    f"L {item['precio']:.2f}",
                    f"L {item['subtotal']:.2f}",
                ),
            )

        total_var.set(f"Total carrito: L {total:.2f}")

    def agregar_al_carrito():
        producto = productos_cache.get(producto_var.get())
        if producto is None:
            messagebox.showwarning("Ventas", "Seleccione un producto.")
            return

        try:
            cantidad = int(cantidad_var.get())
        except ValueError:
            messagebox.showerror("Ventas", "La cantidad debe ser un numero entero.")
            return

        if cantidad <= 0:
            messagebox.showerror("Ventas", "La cantidad debe ser mayor que cero.")
            return

        cantidad_actual_en_carrito = sum(
            item["cantidad"]
            for item in carrito
            if item["producto_id"] == producto["id"]
        )

        if cantidad_actual_en_carrito + cantidad > producto["stock_actual"]:
            messagebox.showerror(
                "Ventas",
                f"No hay suficiente stock. Disponible: {producto['stock_actual']}.",
            )
            return

        for item in carrito:
            if item["producto_id"] == producto["id"]:
                item["cantidad"] += cantidad
                item["subtotal"] = item["cantidad"] * item["precio"]
                refrescar_carrito()
                return

        carrito.append(
            {
                "producto_id": producto["id"],
                "nombre": producto["nombre"],
                "cantidad": cantidad,
                "precio": producto["precio"],
                "subtotal": cantidad * producto["precio"],
            }
        )
        refrescar_carrito()

    def quitar_del_carrito():
        seleccion = tabla_carrito.selection()
        if not seleccion:
            messagebox.showwarning("Ventas", "Seleccione un producto del carrito.")
            return

        producto_id = int(seleccion[0])
        carrito[:] = [
            item for item in carrito if item["producto_id"] != producto_id
        ]
        refrescar_carrito()

    def limpiar_carrito():
        carrito.clear()
        refrescar_carrito()

    def guardar_venta():
        if not carrito:
            messagebox.showwarning("Ventas", "Agregue productos al carrito.")
            return

        ok, mensaje = registrar_venta_multiple(
            cliente_var.get(),
            [
                {
                    "producto_id": item["producto_id"],
                    "cantidad": item["cantidad"],
                }
                for item in carrito
            ],
        )

        if ok:
            messagebox.showinfo("Ventas", mensaje)
            cliente_var.set("")
            cantidad_var.set("1")
            limpiar_carrito()
            cargar_productos()
            cargar_ventas()
        else:
            messagebox.showerror("Ventas", mensaje)

    def obtener_venta_seleccionada():
        seleccion = tabla_ventas.selection()
        if not seleccion:
            messagebox.showwarning("Ventas", "Seleccione una venta registrada.")
            return None

        valores = tabla_ventas.item(seleccion[0], "values")
        return int(valores[0])

    def anular_venta_seleccionada():
        venta_id = obtener_venta_seleccionada()
        if venta_id is None:
            return

        confirmar = messagebox.askyesno(
            "Anular venta",
            "Desea anular la venta seleccionada y devolver el stock?",
        )
        if not confirmar:
            return

        ok, mensaje = anular_venta(venta_id)

        if ok:
            messagebox.showinfo("Ventas", mensaje)
            cargar_productos()
            cargar_ventas()
        else:
            messagebox.showerror("Ventas", mensaje)

    ttk.Button(
        acciones_carrito,
        text="Agregar al carrito",
        command=agregar_al_carrito,
        style="Primary.TButton",
    ).grid(row=0, column=0, sticky=tk.W, padx=(0, 6))
    ttk.Button(
        acciones_carrito,
        text="Quitar item",
        command=quitar_del_carrito,
        style="Warning.TButton",
    ).grid(row=0, column=1, sticky=tk.W, padx=(0, 6))
    ttk.Button(
        acciones_carrito,
        text="Limpiar",
        command=limpiar_carrito,
        style="Info.TButton",
    ).grid(row=0, column=2, sticky=tk.W)
    ttk.Button(
        acciones_venta,
        text="Registrar venta",
        command=guardar_venta,
        style="Accent.TButton",
    ).grid(row=0, column=0, sticky=tk.E, padx=(0, 6))
    ttk.Button(
        acciones_venta,
        text="Anular venta",
        command=anular_venta_seleccionada,
        style="Danger.TButton",
    ).grid(row=0, column=1, sticky=tk.E, padx=(0, 6))
    ttk.Button(
        acciones_venta,
        text="Actualizar",
        command=lambda: (cargar_productos(), cargar_ventas()),
        style="Primary.TButton",
    ).grid(row=0, column=2, sticky=tk.E)

    cargar_productos()
    cargar_ventas()
    refrescar_carrito()

    if standalone:
        raiz.mainloop()


def _normalizar_items(items):
    cantidades_por_producto = {}

    for item in items:
        try:
            producto_id = int(item["producto_id"])
            cantidad = int(item["cantidad"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Los productos de la venta no son validos.") from error

        if cantidad <= 0:
            raise ValueError("Todas las cantidades deben ser mayores que cero.")

        cantidades_por_producto[producto_id] = (
            cantidades_por_producto.get(producto_id, 0) + cantidad
        )

    return [
        {"producto_id": producto_id, "cantidad": cantidad}
        for producto_id, cantidad in cantidades_por_producto.items()
    ]


def _obtener_productos_por_id(conexion, producto_ids):
    productos = {}

    for producto_id in producto_ids:
        producto = conexion.execute(
            """
            SELECT id, nombre, precio, stock_actual
            FROM productos
            WHERE id = ? AND activo = 1
            """,
            (producto_id,),
        ).fetchone()

        if producto:
            productos[producto_id] = producto

    return productos


def _obtener_o_crear_cliente(conexion, nombre):
    nombre = nombre.strip()
    cliente = conexion.execute(
        "SELECT id FROM clientes WHERE LOWER(nombre) = LOWER(?)",
        (nombre,),
    ).fetchone()

    if cliente:
        return cliente["id"]

    cursor = conexion.execute(
        "INSERT INTO clientes (nombre) VALUES (?)",
        (nombre,),
    )
    return cursor.lastrowid
