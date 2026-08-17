import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from app.api_client import get_api_client
from app.api_client.exceptions import ApiNotFoundError, ApiValidationError
from app.database.json_storage import (
    buscar_por_id,
    cargar_todo,
    fecha_actual,
    guardar_todo,
    inicializar_datos_json,
    siguiente_id,
)
from app.ui_theme import aplicar_tema, configurar_tabla, crear_encabezado
from app.validaciones import validar_id_positivo, validar_ruta_exportacion


def crear_tabla_facturas(ruta_db=None):
    if ruta_db is None:
        return None
    inicializar_datos_json(ruta_db)


def generar_factura(venta_id, ruta_db=None):
    if ruta_db is None:
        try:
            venta_id = validar_id_positivo(venta_id, "venta")
            factura = get_api_client().facturas.emitir(venta_id)
        except Exception as error:
            return False, str(error)
        return True, f"Factura {factura['numero']} generada correctamente."

    inicializar_datos_json(ruta_db)

    try:
        venta_id = validar_id_positivo(venta_id, "venta")
    except ValueError as error:
        return False, str(error)

    datos = cargar_todo(ruta_db)
    venta = buscar_por_id(datos["ventas"], venta_id)

    if venta is None:
        return False, "La venta no existe."

    if venta["estado"] != "Completada":
        return False, "Solo se pueden facturar ventas completadas."

    factura = _factura_por_venta(datos["facturas"], venta_id)

    if factura:
        return False, f"La venta ya tiene factura: {factura['numero_factura']}."

    numero_factura = f"FAC-{int(venta_id):06d}"
    datos["facturas"].append(
        {
            "id": siguiente_id("facturas", datos["facturas"]),
            "venta_id": int(venta_id),
            "numero_factura": numero_factura,
            "fecha": fecha_actual(),
            "total": float(venta["total"]),
        }
    )
    guardar_todo({"facturas": datos["facturas"]}, ruta_db)

    return True, f"Factura {numero_factura} generada correctamente."


def obtener_facturas(ruta_db=None):
    if ruta_db is None:
        facturas = [
            _armar_factura_api(factura)
            for factura in get_api_client().facturas.listar_todas()
        ]
        facturas.sort(key=lambda factura: int(factura["id"]), reverse=True)
        return facturas

    datos = cargar_todo(ruta_db)
    facturas = [_armar_factura(factura, datos) for factura in datos["facturas"]]
    facturas.sort(key=lambda factura: int(factura["id"]), reverse=True)
    return facturas


def obtener_factura_por_id(factura_id, ruta_db=None):
    try:
        factura_id = validar_id_positivo(factura_id, "factura")
    except ValueError:
        return None

    if ruta_db is None:
        try:
            return _armar_factura_api(get_api_client().facturas.obtener(factura_id))
        except (ApiNotFoundError, ApiValidationError):
            return None

    datos = cargar_todo(ruta_db)
    factura = buscar_por_id(datos["facturas"], factura_id)
    return _armar_factura(factura, datos) if factura else None


def obtener_factura_por_venta_id(venta_id, ruta_db=None):
    try:
        venta_id = validar_id_positivo(venta_id, "venta")
    except ValueError:
        return None

    if ruta_db is None:
        facturas = get_api_client().facturas.listar_todas(venta_id=venta_id)
        return _armar_factura_api(facturas[0]) if facturas else None

    datos = cargar_todo(ruta_db)
    factura = _factura_por_venta(datos["facturas"], venta_id)
    return _armar_factura(factura, datos) if factura else None


def obtener_detalle_factura(factura_id, ruta_db=None):
    try:
        factura_id = validar_id_positivo(factura_id, "factura")
    except ValueError:
        return []

    if ruta_db is None:
        try:
            factura = get_api_client().facturas.obtener(factura_id)
        except (ApiNotFoundError, ApiValidationError):
            return []
        return [_armar_detalle_factura_api(detalle) for detalle in factura.get("detalles", [])]

    datos = cargar_todo(ruta_db)
    factura = buscar_por_id(datos["facturas"], factura_id)

    if factura is None:
        return []

    detalles = [
        detalle
        for detalle in datos["detalle_venta"]
        if int(detalle["venta_id"]) == int(factura["venta_id"])
    ]
    detalles.sort(key=lambda detalle: int(detalle["id"]))
    return [
        {
            "producto": _nombre_producto(datos["productos"], detalle["producto_id"]),
            "cantidad": int(detalle["cantidad"]),
            "precio_unitario": float(detalle["precio_unitario"]),
            "subtotal": float(detalle["subtotal"]),
        }
        for detalle in detalles
    ]


def obtener_ventas_para_facturar(ruta_db=None):
    if ruta_db is None:
        api = get_api_client()
        ventas_con_factura = {
            int(factura["venta_id"])
            for factura in api.facturas.listar_todas()
        }
        ventas = [
            {
                "id": venta["id"],
                "cliente": venta.get("cliente_nombre"),
                "total": float(venta["total"]),
                "fecha": venta.get("created_at"),
            }
            for venta in api.ventas.listar_todas(estado="COMPLETADA")
            if int(venta["id"]) not in ventas_con_factura
        ]
        ventas.sort(key=lambda venta: int(venta["id"]), reverse=True)
        return ventas

    datos = cargar_todo(ruta_db)
    ventas_con_factura = {
        int(factura["venta_id"])
        for factura in datos["facturas"]
    }
    ventas = [
        {
            "id": venta["id"],
            "cliente": _nombre_cliente(datos["clientes"], venta.get("cliente_id")),
            "total": float(venta["total"]),
            "fecha": venta["fecha"],
        }
        for venta in datos["ventas"]
        if venta["estado"] == "Completada"
        and int(venta["id"]) not in ventas_con_factura
    ]
    ventas.sort(key=lambda venta: int(venta["id"]), reverse=True)
    return ventas


def _armar_factura_api(factura):
    return {
        "id": factura["id"],
        "numero_factura": factura["numero"],
        "venta_id": factura["venta_id"],
        "cliente": factura.get("cliente_nombre"),
        "total": float(factura["total"]),
        "fecha": factura.get("created_at"),
        "estado": factura.get("estado"),
    }


def _armar_detalle_factura_api(detalle):
    return {
        "producto": detalle["producto_nombre"],
        "cantidad": int(detalle["cantidad"]),
        "precio_unitario": float(detalle["precio_unitario"]),
        "subtotal": float(detalle["subtotal"]),
    }


def _armar_factura(factura, datos):
    venta = buscar_por_id(datos["ventas"], factura["venta_id"])
    cliente = None

    if venta:
        cliente = _nombre_cliente(datos["clientes"], venta.get("cliente_id"))

    return {
        "id": factura["id"],
        "numero_factura": factura["numero_factura"],
        "venta_id": factura["venta_id"],
        "cliente": cliente,
        "total": float(factura["total"]),
        "fecha": factura["fecha"],
    }


def _factura_por_venta(facturas, venta_id):
    venta_id = int(venta_id)
    return next(
        (
            factura
            for factura in facturas
            if int(factura["venta_id"]) == venta_id
        ),
        None,
    )


def _nombre_cliente(clientes, cliente_id):
    if cliente_id is None:
        return None

    cliente = buscar_por_id(clientes, cliente_id)
    return cliente["nombre"] if cliente else None


def _nombre_producto(productos, producto_id):
    producto = buscar_por_id(productos, producto_id)
    return producto["nombre"] if producto else f"Producto ID {producto_id}"


def generar_texto_factura(factura_id, ruta_db=None):
    factura_id = validar_id_positivo(factura_id, "factura")
    factura = obtener_factura_por_id(factura_id, ruta_db)
    if factura is None:
        raise ValueError("La factura no existe.")

    detalles = obtener_detalle_factura(factura_id, ruta_db)
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


def exportar_factura_txt(factura_id, ruta_archivo, ruta_db=None):
    ruta_archivo = validar_ruta_exportacion(
        ruta_archivo,
        ".txt",
        "la factura TXT",
    )
    texto = generar_texto_factura(factura_id, ruta_db)

    with open(ruta_archivo, "w", encoding="utf-8") as archivo:
        archivo.write(texto)


def exportar_factura_pdf(factura_id, ruta_archivo, ruta_db=None):
    ruta_archivo = validar_ruta_exportacion(
        ruta_archivo,
        ".pdf",
        "la factura PDF",
    )
    factura = obtener_factura_por_id(factura_id, ruta_db)
    if factura is None:
        raise ValueError("La factura no existe.")

    detalles = obtener_detalle_factura(factura_id, ruta_db)
    cliente = factura["cliente"] or "Sin cliente"
    comandos = []

    _pdf_text(comandos, "Perfum Lab", 36, 748, 17, "F2")
    _pdf_text(comandos, "Sistema de inventario y ventas", 36, 731, 8, "F3")
    _pdf_text(comandos, "Direccion", 36, 705, 8, "F2")
    _pdf_text(comandos, "La Paz, Codigo postal 15101", 36, 693, 8)
    _pdf_text(comandos, "Telefono: 123.456.7890", 36, 681, 8)

    _pdf_text(comandos, "Factura", 445, 745, 29, "F3")
    _pdf_text(comandos, f"FECHA: {str(factura['fecha'])[:10]}", 430, 707, 8, "F2")
    _pdf_text(comandos, f"FACTURA No: {factura['numero_factura']}", 430, 694, 8, "F2")
    _pdf_text(comandos, f"VENTA No: {factura['venta_id']}", 430, 681, 8, "F2")

    _pdf_text(comandos, "Facturar a:", 36, 635, 9, "F2")
    _pdf_line(comandos, 36, 628, 210, 628)
    _pdf_text(comandos, cliente, 36, 615, 8)
    _pdf_text(comandos, "Direccion", 36, 603, 8)
    _pdf_text(comandos, "La Paz, Codigo postal 15101", 36, 591, 8)
    _pdf_text(comandos, "Telefono", 36, 579, 8)

    _pdf_text(comandos, "Enviar a:", 310, 635, 9, "F2")
    _pdf_line(comandos, 310, 628, 484, 628)
    _pdf_text(comandos, cliente, 310, 615, 8)
    _pdf_text(comandos, "Direccion", 310, 603, 8)
    _pdf_text(comandos, "La Paz, Codigo postal 15101", 310, 591, 8)
    _pdf_text(comandos, "Telefono", 310, 579, 8)

    _pdf_text(comandos, "Comentarios o instrucciones especiales:", 36, 545, 8, "F2")
    _pdf_text(comandos, "Ninguno", 230, 545, 8)

    _dibujar_tabla_condiciones(comandos, factura)
    _dibujar_tabla_productos(comandos, detalles, factura["total"])
    _escribir_pdf(ruta_archivo, comandos)


def _escribir_pdf_simple(ruta_archivo, lineas):
    comandos = []
    for texto, tamano, x, y in lineas:
        _pdf_text(comandos, texto, x, y, tamano)
    _escribir_pdf(ruta_archivo, comandos)


def _dibujar_tabla_condiciones(comandos, factura):
    x = 36
    y = 505
    anchos = [82, 105, 102, 105, 90, 56]
    titulos = [
        "VENDEDOR",
        "NUMERO DE O/C",
        "FECHA DE ENVIO",
        "ENVIO MEDIANTE",
        "PUNTO F.O.B.",
        "TERMINOS",
    ]
    valores = [
        "Sistema",
        factura["numero_factura"],
        str(factura["fecha"])[:10],
        "Directo",
        "Perfum Lab",
        "Al recibir",
    ]

    _pdf_fill_rect(comandos, x, y, sum(anchos), 18, 0.72, 0.86, 0.96)
    cursor = x
    for ancho, titulo, valor in zip(anchos, titulos, valores):
        _pdf_rect(comandos, cursor, y, ancho, 36)
        _pdf_text(comandos, titulo, cursor + 5, y + 22, 6.5, "F2")
        _pdf_text(comandos, valor, cursor + 5, y + 7, 7)
        cursor += ancho


def _dibujar_tabla_productos(comandos, detalles, total):
    x = 36
    y = 235
    alto = 235
    columnas = [
        ("CANTIDAD", 78),
        ("DESCRIPCION", 270),
        ("PRECIO UNITARIO", 96),
        ("MONTO", 96),
    ]

    _pdf_fill_rect(comandos, x, y + alto - 18, 540, 18, 0.83, 0.83, 0.83)
    _pdf_rect(comandos, x, y, 540, alto)

    cursor = x
    for titulo, ancho in columnas:
        _pdf_rect(comandos, cursor, y, ancho, alto)
        _pdf_text(comandos, titulo, cursor + 8, y + alto - 12, 7, "F2")
        cursor += ancho

    fila_y = y + alto - 36
    for detalle in detalles[:10]:
        _pdf_text(comandos, str(detalle["cantidad"]), x + 12, fila_y, 9)
        _pdf_text(comandos, str(detalle["producto"])[:45], x + 88, fila_y, 9)
        _pdf_text(comandos, f"L {detalle['precio_unitario']:.2f}", x + 360, fila_y, 9)
        _pdf_text(comandos, f"L {detalle['subtotal']:.2f}", x + 458, fila_y, 9)
        fila_y -= 18

    total_x = 386
    total_y = 105
    filas = [
        ("SUBTOTAL", f"L {total:.2f}"),
        ("TASA DE IMPUESTO", "0.00%"),
        ("IMPUESTO A LAS VENTAS", "L 0.00"),
        ("ENVIO Y MANEJO", "L 0.00"),
        ("TOTAL", f"L {total:.2f}"),
    ]
    for indice, (etiqueta, valor) in enumerate(filas):
        y_fila = total_y + (len(filas) - indice - 1) * 18
        _pdf_text(comandos, etiqueta, total_x, y_fila + 5, 8, "F2")
        _pdf_rect(comandos, total_x + 120, y_fila, 70, 18)
        _pdf_text(comandos, valor, total_x + 126, y_fila + 5, 8)


def _escribir_pdf(ruta_archivo, comandos):
    stream = "\n".join(comandos).encode("latin-1", errors="replace")
    recursos = (
        b"/Resources << /Font << "
        b"/F1 4 0 R /F2 5 0 R /F3 6 0 R "
        b">> >> /Contents 7 0 R >>"
    )

    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] " + recursos,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-BoldOblique >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]

    contenido = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for indice, objeto in enumerate(objetos, start=1):
        offsets.append(len(contenido))
        contenido.extend(f"{indice} 0 obj\n".encode("ascii"))
        contenido.extend(objeto)
        contenido.extend(b"\nendobj\n")

    xref = len(contenido)
    contenido.extend(f"xref\n0 {len(objetos) + 1}\n".encode("ascii"))
    contenido.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        contenido.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    contenido.extend(
        (
            f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref}\n%%EOF"
        ).encode("ascii")
    )

    with open(ruta_archivo, "wb") as archivo:
        archivo.write(contenido)


def _pdf_text(comandos, texto, x, y, tamano=9, fuente="F1"):
    comandos.append("0 0 0 rg")
    comandos.append("BT")
    comandos.append(f"/{fuente} {tamano} Tf")
    comandos.append(f"{x} {y} Td ({_pdf_escape(texto)}) Tj")
    comandos.append("ET")


def _pdf_line(comandos, x1, y1, x2, y2):
    comandos.append("0 0 0 RG")
    comandos.append("0.8 w")
    comandos.append(f"{x1} {y1} m {x2} {y2} l S")


def _pdf_rect(comandos, x, y, ancho, alto):
    comandos.append("0 0 0 RG")
    comandos.append("0.8 w")
    comandos.append(f"{x} {y} {ancho} {alto} re S")


def _pdf_fill_rect(comandos, x, y, ancho, alto, r, g, b):
    comandos.append(f"{r} {g} {b} rg")
    comandos.append(f"{x} {y} {ancho} {alto} re f")


def _pdf_escape(texto):
    return str(texto).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def abrir_facturas(ventana=None):
    standalone = ventana is None
    contenedor = ventana or tk.Tk()
    raiz = contenedor.winfo_toplevel()
    aplicar_tema(raiz)
    raiz.title("Perfum Lab - Facturas")
    raiz.geometry("1180x720")
    raiz.minsize(980, 620)

    frame = ttk.Frame(contenedor, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(4, weight=1)

    venta_var = tk.StringVar()
    resumen_var = tk.StringVar(value="Seleccione una factura para ver su detalle.")
    ventas_cache = {}

    crear_encabezado(
        frame,
        "Facturas",
        "Emite facturas para ventas completadas y exporta comprobantes.",
    )

    formulario = ttk.Frame(frame, style="Toolbar.TFrame", padding=(12, 10))
    formulario.grid(row=1, column=0, sticky="ew", pady=(0, 10))
    formulario.columnconfigure(1, weight=1)

    ttk.Label(
        formulario,
        text="Venta pendiente",
        style="Toolbar.TLabel",
    ).grid(row=0, column=0, sticky=tk.W)
    venta_combo = ttk.Combobox(formulario, textvariable=venta_var, state="readonly")
    venta_combo.grid(row=0, column=1, sticky="ew", padx=(8, 8))
    generar_btn = ttk.Button(
        formulario,
        text="Generar factura PDF",
        command=lambda: guardar_factura(),
        style="Primary.TButton",
    )
    generar_btn.grid(row=0, column=2, sticky=tk.E)

    botones = ttk.Frame(frame)
    botones.grid(row=2, column=0, sticky="ew", pady=(0, 8))
    botones.columnconfigure(1, weight=1)

    acciones_consulta = ttk.Frame(botones)
    acciones_consulta.grid(row=0, column=0, sticky=tk.W)
    acciones_factura = ttk.Frame(botones)
    acciones_factura.grid(row=0, column=2, sticky=tk.E)

    ttk.Label(frame, text="Facturas emitidas", style="Section.TLabel").grid(
        row=3,
        column=0,
        sticky=tk.W,
        pady=(2, 6),
    )

    panel = ttk.PanedWindow(frame, orient=tk.VERTICAL)
    panel.grid(row=4, column=0, sticky="nsew")

    facturas_frame = ttk.Frame(panel)
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

    configurar_tabla(tabla_facturas)
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

    configurar_tabla(tabla_detalle)
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

        try:
            ventas = obtener_ventas_para_facturar()
        except Exception as error:
            messagebox.showerror("Facturas", str(error))
            return

        for venta in ventas:
            cliente = venta["cliente"] or "Sin cliente"
            etiqueta = f"{venta['id']} - {cliente} - L {venta['total']:.2f}"
            ventas_cache[etiqueta] = venta["id"]
            opciones.append(etiqueta)

        venta_combo["values"] = opciones
        venta_var.set(opciones[0] if opciones else "")

    def cargar_facturas():
        for item in tabla_facturas.get_children():
            tabla_facturas.delete(item)

        try:
            facturas = obtener_facturas()
        except Exception as error:
            messagebox.showerror("Facturas", str(error))
            return

        for indice, factura in enumerate(facturas):
            tabla_facturas.insert(
                "",
                tk.END,
                iid=str(factura["id"]),
                tags=("even" if indice % 2 else "odd",),
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

        try:
            factura = obtener_factura_por_id(factura_id)
            detalles = obtener_detalle_factura(factura_id)
        except Exception as error:
            messagebox.showerror("Facturas", str(error))
            return

        if factura is None:
            resumen_var.set("Seleccione una factura para ver su detalle.")
            return

        cliente = factura["cliente"] or "Sin cliente"
        resumen_var.set(
            f"{factura['numero_factura']} | Venta #{factura['venta_id']} | "
            f"Cliente: {cliente} | Total: L {factura['total']:.2f}"
        )

        for indice, detalle in enumerate(detalles):
            tabla_detalle.insert(
                "",
                tk.END,
                tags=("even" if indice % 2 else "odd",),
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

        generar_btn.state(["disabled"])
        try:
            ok, mensaje = generar_factura(venta_id)
        finally:
            generar_btn.state(["!disabled"])

        if ok:
            try:
                factura = obtener_factura_por_venta_id(venta_id)
                cargar_ventas_pendientes()
                cargar_facturas()
            except Exception as error:
                messagebox.showerror("Facturas", str(error))
                return
            if factura is not None:
                tabla_facturas.selection_set(str(factura["id"]))
                tabla_facturas.focus(str(factura["id"]))
                cargar_detalle_factura(factura["id"])
                exportar_factura_pdf_con_dialogo(factura["id"], mensaje)
            else:
                messagebox.showinfo("Facturas", mensaje)
        else:
            messagebox.showerror("Facturas", mensaje)

    def obtener_factura_id_seleccionada():
        seleccion = tabla_facturas.selection()
        if not seleccion:
            messagebox.showwarning("Facturas", "Seleccione una factura.")
            return None

        return int(seleccion[0])

    def exportar_factura_pdf_con_dialogo(factura_id, mensaje_exito=None):
        try:
            factura = obtener_factura_por_id(factura_id)
        except Exception as error:
            messagebox.showerror("Facturas", str(error))
            return

        if factura is None:
            messagebox.showerror("Facturas", "La factura seleccionada no existe.")
            return

        ruta_archivo = filedialog.asksaveasfilename(
            parent=raiz,
            title="Guardar factura PDF",
            defaultextension=".pdf",
            initialfile=f"{factura['numero_factura']}.pdf",
            filetypes=(("PDF", "*.pdf"), ("Todos los archivos", "*.*")),
        )

        if not ruta_archivo:
            if mensaje_exito:
                messagebox.showinfo("Facturas", mensaje_exito)
            return

        try:
            exportar_factura_pdf(factura_id, ruta_archivo)
            mensaje = mensaje_exito or "Factura exportada correctamente."
            messagebox.showinfo("Facturas", f"{mensaje}\nPDF guardado correctamente.")
        except Exception as error:
            messagebox.showerror("Facturas", str(error))

    def exportar_factura_seleccionada():
        factura_id = obtener_factura_id_seleccionada()
        if factura_id is None:
            return

        exportar_factura_pdf_con_dialogo(factura_id)

    def actualizar_todo():
        cargar_ventas_pendientes()
        cargar_facturas()

    tabla_facturas.bind("<<TreeviewSelect>>", al_seleccionar_factura)

    ttk.Button(
        acciones_consulta,
        text="Ver detalle",
        command=al_seleccionar_factura,
        style="Info.TButton",
    ).grid(row=0, column=0, sticky=tk.W, padx=(0, 6))
    ttk.Button(
        acciones_factura,
        text="Exportar PDF",
        command=exportar_factura_seleccionada,
        style="Accent.TButton",
    ).grid(row=0, column=0, sticky=tk.E)
    ttk.Button(
        acciones_consulta,
        text="Actualizar",
        command=actualizar_todo,
        style="Primary.TButton",
    ).grid(row=0, column=1, sticky=tk.W)

    cargar_ventas_pendientes()
    cargar_facturas()

    if standalone:
        raiz.mainloop()
