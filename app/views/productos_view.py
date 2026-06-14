import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from app.controllers.inventario_controller import InventarioController
from app.controllers.productos_controller import ProductosController
from app.models.producto import Producto


class ProductosView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.productos_controller = ProductosController()
        self.inventario_controller = InventarioController()
        self.producto_seleccionado_id = None

        self.sku_var = tk.StringVar()
        self.nombre_var = tk.StringVar()
        self.marca_var = tk.StringVar()
        self.costo_var = tk.StringVar(value="0")
        self.precio_var = tk.StringVar(value="0")
        self.stock_var = tk.StringVar(value="0")
        self.stock_minimo_var = tk.StringVar(value="0")
        self.filtrar_movimientos_var = tk.BooleanVar(value=False)
        self.descripcion_text = None

        self._crear_widgets()
        self.cargar_productos()
        self.cargar_movimientos()

    def _crear_widgets(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        contenedor = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        contenedor.grid(row=0, column=0, sticky="nsew")

        tabla_frame = ttk.Frame(contenedor)
        formulario_frame = ttk.Frame(contenedor, padding=(10, 0, 0, 0))
        contenedor.add(tabla_frame, weight=3)
        contenedor.add(formulario_frame, weight=2)

        self._crear_tablas(tabla_frame)
        self._crear_formulario(formulario_frame)
        self._crear_botones(formulario_frame)

    def _crear_tablas(self, contenedor):
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(0, weight=1)

        tablas = ttk.PanedWindow(contenedor, orient=tk.VERTICAL)
        tablas.grid(row=0, column=0, sticky="nsew")

        productos_frame = ttk.Frame(tablas)
        movimientos_frame = ttk.Frame(tablas)
        tablas.add(productos_frame, weight=3)
        tablas.add(movimientos_frame, weight=2)

        self._crear_tabla_productos(productos_frame)
        self._crear_tabla_movimientos(movimientos_frame)

    def _crear_tabla_productos(self, contenedor):
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(1, weight=1)

        ttk.Label(contenedor, text="Productos").grid(
            row=0,
            column=0,
            columnspan=2,
            sticky=tk.W,
            pady=(0, 4),
        )

        columnas = ("id", "sku", "nombre", "marca", "stock", "precio")
        self.tabla = ttk.Treeview(
            contenedor,
            columns=columnas,
            show="headings",
            selectmode="browse",
        )

        encabezados = {
            "id": "ID",
            "sku": "SKU",
            "nombre": "Nombre",
            "marca": "Marca",
            "stock": "Stock",
            "precio": "Precio",
        }

        anchos = {
            "id": 50,
            "sku": 100,
            "nombre": 180,
            "marca": 120,
            "stock": 80,
            "precio": 90,
        }

        for columna in columnas:
            self.tabla.heading(columna, text=encabezados[columna])
            self.tabla.column(columna, width=anchos[columna], anchor=tk.W)

        scroll = ttk.Scrollbar(
            contenedor,
            orient=tk.VERTICAL,
            command=self.tabla.yview,
        )
        self.tabla.configure(yscrollcommand=scroll.set)

        self.tabla.grid(row=1, column=0, sticky="nsew")
        scroll.grid(row=1, column=1, sticky="ns")
        self.tabla.bind("<<TreeviewSelect>>", self._al_seleccionar_producto)

    def _crear_tabla_movimientos(self, contenedor):
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(1, weight=1)

        encabezado = ttk.Frame(contenedor)
        encabezado.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(8, 4))
        encabezado.columnconfigure(0, weight=1)

        ttk.Label(encabezado, text="Movimientos de inventario").grid(
            row=0,
            column=0,
            sticky=tk.W,
        )
        ttk.Button(
            encabezado,
            text="Actualizar movimientos",
            command=self.cargar_movimientos,
        ).grid(row=0, column=1, sticky=tk.E)
        ttk.Checkbutton(
            encabezado,
            text="Solo producto seleccionado",
            variable=self.filtrar_movimientos_var,
            command=self.cargar_movimientos,
        ).grid(row=0, column=2, sticky=tk.E, padx=(8, 0))

        columnas = (
            "id",
            "producto",
            "tipo",
            "cantidad",
            "stock_anterior",
            "stock_nuevo",
            "motivo",
            "fecha",
        )
        self.tabla_movimientos = ttk.Treeview(
            contenedor,
            columns=columnas,
            show="headings",
            selectmode="browse",
        )

        encabezados = {
            "id": "ID",
            "producto": "Producto",
            "tipo": "Tipo",
            "cantidad": "Cantidad",
            "stock_anterior": "Stock anterior",
            "stock_nuevo": "Stock nuevo",
            "motivo": "Motivo",
            "fecha": "Fecha",
        }

        anchos = {
            "id": 50,
            "producto": 160,
            "tipo": 90,
            "cantidad": 80,
            "stock_anterior": 110,
            "stock_nuevo": 100,
            "motivo": 180,
            "fecha": 140,
        }

        for columna in columnas:
            self.tabla_movimientos.heading(columna, text=encabezados[columna])
            self.tabla_movimientos.column(
                columna,
                width=anchos[columna],
                anchor=tk.W,
            )

        scroll_y = ttk.Scrollbar(
            contenedor,
            orient=tk.VERTICAL,
            command=self.tabla_movimientos.yview,
        )
        scroll_x = ttk.Scrollbar(
            contenedor,
            orient=tk.HORIZONTAL,
            command=self.tabla_movimientos.xview,
        )
        self.tabla_movimientos.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
        )

        self.tabla_movimientos.grid(row=1, column=0, sticky="nsew")
        scroll_y.grid(row=1, column=1, sticky="ns")
        scroll_x.grid(row=2, column=0, sticky="ew")

    def _crear_formulario(self, contenedor):
        contenedor.columnconfigure(1, weight=1)

        ttk.Label(contenedor, text="Datos del producto").grid(
            row=0,
            column=0,
            columnspan=2,
            sticky=tk.W,
            pady=(0, 8),
        )

        campos = [
            ("SKU", self.sku_var),
            ("Nombre", self.nombre_var),
            ("Marca", self.marca_var),
            ("Costo", self.costo_var),
            ("Precio", self.precio_var),
            ("Stock actual", self.stock_var),
            ("Stock minimo", self.stock_minimo_var),
        ]

        for indice, (etiqueta, variable) in enumerate(campos, start=1):
            ttk.Label(contenedor, text=etiqueta).grid(
                row=indice,
                column=0,
                sticky=tk.W,
                pady=3,
            )
            ttk.Entry(contenedor, textvariable=variable).grid(
                row=indice,
                column=1,
                sticky="ew",
                pady=3,
            )

        ttk.Label(contenedor, text="Descripcion").grid(
            row=8,
            column=0,
            sticky=tk.NW,
            pady=3,
        )
        self.descripcion_text = tk.Text(contenedor, height=4, width=30)
        self.descripcion_text.grid(row=8, column=1, sticky="ew", pady=3)

    def _crear_botones(self, contenedor):
        botones_frame = ttk.Frame(contenedor)
        botones_frame.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        acciones = [
            ("Nuevo", self.limpiar_formulario),
            ("Guardar", self.guardar_producto),
            ("Eliminar", self.eliminar_producto),
            ("Entrada", self.registrar_entrada),
            ("Salida", self.registrar_salida),
            ("Ajuste", self.registrar_ajuste),
            ("Actualizar", self.cargar_productos),
            ("Actualizar movimientos", self.cargar_movimientos),
        ]

        for indice, (texto, comando) in enumerate(acciones):
            boton = ttk.Button(botones_frame, text=texto, command=comando)
            boton.grid(row=indice // 2, column=indice % 2, sticky="ew", padx=3, pady=3)

        botones_frame.columnconfigure(0, weight=1)
        botones_frame.columnconfigure(1, weight=1)

    def cargar_productos(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        productos = self.productos_controller.listar_productos()

        for producto in productos:
            self.tabla.insert(
                "",
                tk.END,
                iid=str(producto.id),
                values=(
                    producto.id,
                    producto.sku,
                    producto.nombre,
                    producto.marca,
                    producto.stock_actual,
                    f"{producto.precio:.2f}",
                ),
            )

    def cargar_movimientos(self):
        for item in self.tabla_movimientos.get_children():
            self.tabla_movimientos.delete(item)

        producto_id = self._obtener_producto_id_para_filtro()
        movimientos = self.inventario_controller.obtener_movimientos(producto_id)
        productos_cache = {}

        for movimiento in movimientos:
            producto_id = movimiento["producto_id"]
            if producto_id not in productos_cache:
                producto = self.productos_controller.obtener_producto(producto_id)
                productos_cache[producto_id] = (
                    producto.nombre if producto else f"Producto ID {producto_id}"
                )

            self.tabla_movimientos.insert(
                "",
                tk.END,
                iid=str(movimiento["id"]),
                values=(
                    movimiento["id"],
                    productos_cache[producto_id],
                    movimiento["tipo_movimiento"],
                    movimiento["cantidad"],
                    movimiento["stock_anterior"],
                    movimiento["stock_nuevo"],
                    movimiento["motivo"],
                    movimiento["fecha"],
                ),
            )

    def guardar_producto(self):
        try:
            producto = self._leer_producto_desde_formulario()

            if self.producto_seleccionado_id is None:
                self.productos_controller.crear_producto(producto)
                mensaje = "Producto agregado correctamente."
            else:
                self.productos_controller.actualizar_producto(
                    self.producto_seleccionado_id,
                    producto,
                )
                mensaje = "Producto actualizado correctamente."

            self.cargar_productos()
            self.limpiar_formulario()
            messagebox.showinfo("Productos", mensaje)
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def eliminar_producto(self):
        producto_id = self._obtener_producto_id_seleccionado()
        if producto_id is None:
            return

        confirmar = messagebox.askyesno(
            "Eliminar producto",
            "Desea desactivar el producto seleccionado?",
        )
        if not confirmar:
            return

        try:
            self.productos_controller.eliminar_producto(producto_id)
            self.cargar_productos()
            self.limpiar_formulario()
            messagebox.showinfo("Productos", "Producto desactivado correctamente.")
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def registrar_entrada(self):
        producto_id = self._obtener_producto_id_seleccionado()
        if producto_id is None:
            return

        cantidad = self._pedir_entero(
            "Entrada de inventario",
            "Cantidad a ingresar:",
            minvalue=1,
        )
        if cantidad is None:
            return

        motivo = self._pedir_motivo("Motivo de la entrada:")

        try:
            self.inventario_controller.registrar_entrada(producto_id, cantidad, motivo)
            self._refrescar_producto_seleccionado(producto_id)
            self.cargar_movimientos()
            messagebox.showinfo("Inventario", "Entrada registrada correctamente.")
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def registrar_salida(self):
        producto_id = self._obtener_producto_id_seleccionado()
        if producto_id is None:
            return

        cantidad = self._pedir_entero(
            "Salida de inventario",
            "Cantidad a retirar:",
            minvalue=1,
        )
        if cantidad is None:
            return

        motivo = self._pedir_motivo("Motivo de la salida:")

        try:
            self.inventario_controller.registrar_salida(producto_id, cantidad, motivo)
            self._refrescar_producto_seleccionado(producto_id)
            self.cargar_movimientos()
            messagebox.showinfo("Inventario", "Salida registrada correctamente.")
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def registrar_ajuste(self):
        producto_id = self._obtener_producto_id_seleccionado()
        if producto_id is None:
            return

        nuevo_stock = self._pedir_entero(
            "Ajuste de stock",
            "Nuevo stock:",
            minvalue=0,
        )
        if nuevo_stock is None:
            return

        motivo = self._pedir_motivo("Motivo del ajuste:")

        try:
            self.inventario_controller.registrar_ajuste(
                producto_id,
                nuevo_stock,
                motivo,
            )
            self._refrescar_producto_seleccionado(producto_id)
            self.cargar_movimientos()
            messagebox.showinfo("Inventario", "Ajuste registrado correctamente.")
        except Exception as error:
            messagebox.showerror("Error", str(error))

    def limpiar_formulario(self):
        self.producto_seleccionado_id = None
        self.sku_var.set("")
        self.nombre_var.set("")
        self.marca_var.set("")
        self.costo_var.set("0")
        self.precio_var.set("0")
        self.stock_var.set("0")
        self.stock_minimo_var.set("0")
        self.descripcion_text.delete("1.0", tk.END)
        self.tabla.selection_remove(self.tabla.selection())

    def _al_seleccionar_producto(self, _evento):
        producto_id = self._obtener_producto_id_seleccionado(mostrar_error=False)
        if producto_id is None:
            return

        producto = self.productos_controller.obtener_producto(producto_id)
        if producto is None:
            return

        self.producto_seleccionado_id = producto.id
        self.sku_var.set(producto.sku)
        self.nombre_var.set(producto.nombre)
        self.marca_var.set(producto.marca)
        self.costo_var.set(str(producto.costo))
        self.precio_var.set(str(producto.precio))
        self.stock_var.set(str(producto.stock_actual))
        self.stock_minimo_var.set(str(producto.stock_minimo))
        self.descripcion_text.delete("1.0", tk.END)
        self.descripcion_text.insert("1.0", producto.descripcion)
        if self.filtrar_movimientos_var.get():
            self.cargar_movimientos()

    def _leer_producto_desde_formulario(self):
        stock_actual = self._convertir_entero(self.stock_var.get(), "Stock actual")

        if self.producto_seleccionado_id is not None:
            producto_actual = self.productos_controller.obtener_producto(
                self.producto_seleccionado_id
            )
            stock_actual = producto_actual.stock_actual

        producto = Producto(
            sku=self.sku_var.get(),
            nombre=self.nombre_var.get(),
            marca=self.marca_var.get(),
            descripcion=self.descripcion_text.get("1.0", tk.END).strip(),
            costo=self._convertir_decimal(self.costo_var.get(), "Costo"),
            precio=self._convertir_decimal(self.precio_var.get(), "Precio"),
            stock_actual=stock_actual,
            stock_minimo=self._convertir_entero(
                self.stock_minimo_var.get(),
                "Stock minimo",
            ),
        )
        producto.validar()
        return producto

    def _obtener_producto_id_seleccionado(self, mostrar_error=True):
        seleccion = self.tabla.selection()

        if not seleccion:
            if mostrar_error:
                messagebox.showwarning("Productos", "Seleccione un producto.")
            return None

        return int(seleccion[0])

    def _obtener_producto_id_para_filtro(self):
        if not self.filtrar_movimientos_var.get():
            return None

        return self._obtener_producto_id_seleccionado(mostrar_error=False)

    def _refrescar_producto_seleccionado(self, producto_id):
        self.cargar_productos()
        if self.tabla.exists(str(producto_id)):
            self.tabla.selection_set(str(producto_id))
            self.tabla.focus(str(producto_id))
            self._al_seleccionar_producto(None)

    def _pedir_entero(self, titulo, mensaje, minvalue):
        return simpledialog.askinteger(
            titulo,
            mensaje,
            parent=self,
            minvalue=minvalue,
        )

    def _pedir_motivo(self, mensaje):
        return simpledialog.askstring(
            "Motivo",
            mensaje,
            parent=self,
        ) or ""

    def _convertir_decimal(self, valor, campo):
        try:
            return float(valor or 0)
        except ValueError as error:
            raise ValueError(f"{campo} debe ser un numero valido.") from error

    def _convertir_entero(self, valor, campo):
        try:
            return int(valor or 0)
        except ValueError as error:
            raise ValueError(f"{campo} debe ser un numero entero valido.") from error


def abrir_productos(root=None):
    ventana = root or tk.Tk()
    ventana.title("Productos e inventario")
    ventana.geometry("980x520")

    vista = ProductosView(ventana)
    vista.pack(fill=tk.BOTH, expand=True)

    if root is None:
        ventana.mainloop()

    return vista
