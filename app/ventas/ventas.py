import tkinter as tk
from tkinter import messagebox, ttk

from app.database.json_storage import (
    DATABASE_PATH,
    buscar_por_id,
    cargar_tabla,
    cargar_todo,
    es_activo,
    fecha_actual,
    guardar_todo,
    inicializar_datos_json,
    siguiente_id,
)
from app.ui_theme import aplicar_tema, configurar_tabla, crear_encabezado
from app.validaciones import (
    validar_entero_positivo,
    validar_id_positivo,
    validar_nombre_cliente,
)


def crear_tabla_ventas(ruta_db=DATABASE_PATH):
    inicializar_datos_json(ruta_db)


def obtener_productos_para_venta(ruta_db=DATABASE_PATH):
    productos = [
        {
            "id": producto["id"],
            "sku": producto["sku"],
            "nombre": producto["nombre"],
            "precio": float(producto["precio"]),
            "stock_actual": int(producto["stock_actual"]),
        }
        for producto in cargar_tabla("productos", ruta_db)
        if es_activo(producto)
    ]
    productos.sort(key=lambda producto: producto["nombre"].lower())
    return productos


def registrar_venta(producto_id, cliente, cantidad, usuario_id=1, ruta_db=DATABASE_PATH):
    return registrar_venta_multiple(
        cliente,
        [{"producto_id": producto_id, "cantidad": cantidad}],
        usuario_id=usuario_id,
        ruta_db=ruta_db,
    )


def registrar_venta_multiple(cliente, items, usuario_id=1, ruta_db=DATABASE_PATH):
    inicializar_datos_json(ruta_db)

    try:
        cliente = validar_nombre_cliente(cliente)
        usuario_id = validar_id_positivo(usuario_id, "usuario")
        items_normalizados = _normalizar_items(items)
    except ValueError as error:
        return False, str(error)

    if not items_normalizados:
        return False, "Debe agregar al menos un producto a la venta."

    datos = cargar_todo(ruta_db)
    productos = _obtener_productos_por_id(
        datos["productos"],
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

    cliente_id = _obtener_o_crear_cliente(datos["clientes"], cliente)
    venta_id = siguiente_id("ventas", datos["ventas"])
    datos["ventas"].append(
        {
            "id": venta_id,
            "cliente_id": cliente_id,
                "usuario_id": usuario_id,
            "fecha": fecha_actual(),
            "total": float(total),
            "estado": "Completada",
        }
    )

    siguiente_detalle_id = siguiente_id("detalle_venta", datos["detalle_venta"])
    siguiente_movimiento_id = siguiente_id(
        "movimientos_inventario",
        datos["movimientos_inventario"],
    )

    for detalle in detalles:
        producto = detalle["producto"]

        datos["detalle_venta"].append(
            {
                "id": siguiente_detalle_id,
                "venta_id": venta_id,
                "producto_id": producto["id"],
                "cantidad": detalle["cantidad"],
                "precio_unitario": detalle["precio"],
                "subtotal": detalle["subtotal"],
            }
        )
        siguiente_detalle_id += 1

        producto["stock_actual"] = detalle["stock_nuevo"]
        producto["fecha_actualizacion"] = fecha_actual()

        datos["movimientos_inventario"].append(
            {
                "id": siguiente_movimiento_id,
                "producto_id": producto["id"],
                "tipo_movimiento": "SALIDA",
                "cantidad": detalle["cantidad"],
                "stock_anterior": detalle["stock_anterior"],
                "stock_nuevo": detalle["stock_nuevo"],
                "motivo": f"Venta #{venta_id} - {cliente.strip()}",
                "fecha": fecha_actual(),
            }
        )
        siguiente_movimiento_id += 1

    guardar_todo(
        {
            "clientes": datos["clientes"],
            "ventas": datos["ventas"],
            "detalle_venta": datos["detalle_venta"],
            "productos": datos["productos"],
            "movimientos_inventario": datos["movimientos_inventario"],
        },
        ruta_db,
    )

    return True, f"Venta #{venta_id} registrada correctamente. Total: L {total:.2f}"


def anular_venta(venta_id, ruta_db=DATABASE_PATH):
    inicializar_datos_json(ruta_db)

    try:
        venta_id = validar_id_positivo(venta_id, "venta")
    except ValueError as error:
        return False, str(error)

    datos = cargar_todo(ruta_db)
    venta = buscar_por_id(datos["ventas"], venta_id)

    if venta is None:
        return False, "La venta no existe."

    if venta["estado"] == "Anulada":
        return False, "La venta ya esta anulada."

    factura = next(
        (
            factura
            for factura in datos["facturas"]
            if int(factura["venta_id"]) == int(venta_id)
        ),
        None,
    )

    if factura is not None:
        return False, "No se puede anular una venta que ya tiene factura."

    detalles = [
        detalle
        for detalle in datos["detalle_venta"]
        if int(detalle["venta_id"]) == int(venta_id)
    ]

    if not detalles:
        return False, "La venta no tiene detalle de productos."

    siguiente_movimiento_id = siguiente_id(
        "movimientos_inventario",
        datos["movimientos_inventario"],
    )

    for detalle in detalles:
        producto = buscar_por_id(datos["productos"], detalle["producto_id"])

        if producto is None:
            return False, f"El producto {detalle['producto_id']} no existe."

        stock_anterior = int(producto["stock_actual"])
        cantidad = int(detalle["cantidad"])
        stock_nuevo = stock_anterior + cantidad
        producto["stock_actual"] = stock_nuevo
        producto["fecha_actualizacion"] = fecha_actual()

        datos["movimientos_inventario"].append(
            {
                "id": siguiente_movimiento_id,
                "producto_id": detalle["producto_id"],
                "tipo_movimiento": "ENTRADA",
                "cantidad": cantidad,
                "stock_anterior": stock_anterior,
                "stock_nuevo": stock_nuevo,
                "motivo": f"Anulacion de venta #{venta_id}",
                "fecha": fecha_actual(),
            }
        )
        siguiente_movimiento_id += 1

    venta["estado"] = "Anulada"
    guardar_todo(
        {
            "ventas": datos["ventas"],
            "productos": datos["productos"],
            "movimientos_inventario": datos["movimientos_inventario"],
        },
        ruta_db,
    )

    return True, f"Venta #{venta_id} anulada correctamente. Stock devuelto."


def obtener_ventas(ruta_db=DATABASE_PATH):
    datos = cargar_todo(ruta_db)
    ventas = [
        _armar_resumen_venta(venta, datos)
        for venta in datos["ventas"]
        if _detalles_de_venta(datos["detalle_venta"], venta["id"])
    ]
    ventas.sort(key=lambda venta: int(venta["id"]), reverse=True)
    return ventas


def obtener_detalle_venta(venta_id, ruta_db=DATABASE_PATH):
    datos = cargar_todo(ruta_db)
    detalles = _detalles_de_venta(datos["detalle_venta"], venta_id)
    detalles.sort(key=lambda detalle: int(detalle["id"]))
    return [
        {
            "id": detalle["id"],
            "venta_id": detalle["venta_id"],
            "producto": _nombre_producto(datos["productos"], detalle["producto_id"]),
            "cantidad": int(detalle["cantidad"]),
            "precio_unitario": float(detalle["precio_unitario"]),
            "subtotal": float(detalle["subtotal"]),
        }
        for detalle in detalles
    ]


def buscar_venta_por_id(venta_id, ruta_db=DATABASE_PATH):
    datos = cargar_todo(ruta_db)
    venta = buscar_por_id(datos["ventas"], venta_id)

    if venta is None:
        return None

    return _armar_resumen_venta(venta, datos)


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
    if not items:
        return []

    cantidades_por_producto = {}

    for item in items:
        try:
            producto_id = item["producto_id"]
            cantidad = item["cantidad"]
        except (KeyError, TypeError) as error:
            raise ValueError("Los productos de la venta no son validos.") from error

        producto_id = validar_id_positivo(producto_id, "producto")
        cantidad = validar_entero_positivo(cantidad, "La cantidad")

        cantidades_por_producto[producto_id] = (
            cantidades_por_producto.get(producto_id, 0) + cantidad
        )

    return [
        {"producto_id": producto_id, "cantidad": cantidad}
        for producto_id, cantidad in cantidades_por_producto.items()
    ]


def _obtener_productos_por_id(productos_disponibles, producto_ids):
    productos = {}

    for producto_id in producto_ids:
        producto = buscar_por_id(productos_disponibles, producto_id)

        if producto and es_activo(producto):
            productos[producto_id] = producto

    return productos


def _obtener_o_crear_cliente(clientes, nombre):
    nombre = validar_nombre_cliente(nombre)
    cliente = next(
        (
            cliente
            for cliente in clientes
            if cliente["nombre"].strip().lower() == nombre.lower()
        ),
        None,
    )

    if cliente:
        return cliente["id"]

    cliente_id = siguiente_id("clientes", clientes)
    clientes.append(
        {
            "id": cliente_id,
            "nombre": nombre,
            "telefono": "",
            "direccion": "",
            "activo": 1,
            "fecha_creacion": fecha_actual(),
            "fecha_actualizacion": None,
        }
    )
    return cliente_id


def _armar_resumen_venta(venta, datos):
    detalles = _detalles_de_venta(datos["detalle_venta"], venta["id"])
    productos = [
        f"{_nombre_producto(datos['productos'], detalle['producto_id'])} x{detalle['cantidad']}"
        for detalle in detalles
    ]
    cantidad_total = sum(int(detalle["cantidad"]) for detalle in detalles)

    return {
        "id": venta["id"],
        "producto": ", ".join(productos),
        "cliente": _nombre_cliente(datos["clientes"], venta.get("cliente_id")),
        "cantidad": cantidad_total,
        "precio_unitario": None,
        "total": float(venta["total"]),
        "estado": venta["estado"],
        "fecha": venta["fecha"],
    }


def _detalles_de_venta(detalles, venta_id):
    venta_id = int(venta_id)
    return [
        detalle
        for detalle in detalles
        if int(detalle["venta_id"]) == venta_id
    ]


def _nombre_cliente(clientes, cliente_id):
    if cliente_id is None:
        return None

    cliente = buscar_por_id(clientes, cliente_id)
    return cliente["nombre"] if cliente else None


def _nombre_producto(productos, producto_id):
    producto = buscar_por_id(productos, producto_id)
    return producto["nombre"] if producto else f"Producto ID {producto_id}"
