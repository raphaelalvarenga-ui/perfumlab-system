import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.clientes_controller import ClientesController
from app.models.cliente import Cliente
from app.ui_theme import aplicar_tema, configurar_tabla, crear_encabezado


class ClientesView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.clientes_controller = ClientesController()
        self.cliente_seleccionado_id = None

        self.busqueda_var = tk.StringVar()
        self.nombre_var = tk.StringVar()
        self.correo_var = tk.StringVar()
        self.telefono_var = tk.StringVar()
        self.direccion_var = tk.StringVar()
        self.activo_var = tk.BooleanVar(value=True)
        self.estado_var = tk.StringVar(value="0 clientes")

        self._crear_widgets()
        self.cargar_clientes()

    def _crear_widgets(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        crear_encabezado(
            self,
            "Clientes",
            "Registra, busca y mantiene correos de clientes.",
        )
        self._crear_barra_busqueda()

        contenedor = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        contenedor.grid(row=2, column=0, sticky="nsew")

        tabla_frame = ttk.Frame(contenedor)
        formulario_frame = ttk.Frame(contenedor, padding=(14, 0, 0, 0))
        contenedor.add(tabla_frame, weight=3)
        contenedor.add(formulario_frame, weight=2)

        self._crear_tabla(tabla_frame)
        self._crear_formulario(formulario_frame)

    def _crear_barra_busqueda(self):
        barra = ttk.Frame(self, style="Toolbar.TFrame", padding=(12, 10))
        barra.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        barra.columnconfigure(1, weight=1)

        ttk.Label(barra, text="Buscar", style="Toolbar.TLabel").grid(
            row=0,
            column=0,
            sticky=tk.W,
            padx=(0, 8),
        )
        busqueda = ttk.Entry(barra, textvariable=self.busqueda_var)
        busqueda.grid(row=0, column=1, sticky="ew")
        busqueda.bind("<Return>", lambda _evento: self.cargar_clientes())
        busqueda.bind("<Escape>", lambda _evento: self._limpiar_busqueda())

        ttk.Button(
            barra,
            text="Filtrar",
            command=self.cargar_clientes,
            style="Primary.TButton",
        ).grid(row=0, column=2, sticky=tk.E, padx=(8, 0))
        ttk.Button(
            barra,
            text="Limpiar",
            command=self._limpiar_busqueda,
            style="Warning.TButton",
        ).grid(row=0, column=3, sticky=tk.E, padx=(6, 0))

    def _crear_tabla(self, contenedor):
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(1, weight=1)

        ttk.Label(contenedor, text="Lista de clientes", style="Section.TLabel").grid(
            row=0,
            column=0,
            columnspan=2,
            sticky=tk.W,
            pady=(0, 6),
        )

        columnas = ("id", "nombre", "correo", "telefono", "estado")
        self.tabla = ttk.Treeview(
            contenedor,
            columns=columnas,
            show="headings",
            selectmode="browse",
        )
        encabezados = {
            "id": "ID",
            "nombre": "Nombre",
            "correo": "Correo electronico",
            "telefono": "Telefono",
            "estado": "Estado",
        }
        anchos = {
            "id": 55,
            "nombre": 170,
            "correo": 220,
            "telefono": 120,
            "estado": 90,
        }

        for columna in columnas:
            self.tabla.heading(columna, text=encabezados[columna])
            self.tabla.column(columna, width=anchos[columna], anchor=tk.W)

        configurar_tabla(self.tabla)
        scroll = ttk.Scrollbar(contenedor, orient=tk.VERTICAL, command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll.set)
        self.tabla.grid(row=1, column=0, sticky="nsew")
        scroll.grid(row=1, column=1, sticky="ns")
        self.tabla.bind("<<TreeviewSelect>>", self._al_seleccionar_cliente)

    def _crear_formulario(self, contenedor):
        contenedor.columnconfigure(1, weight=1)

        resumen = ttk.Frame(contenedor, style="Surface.TFrame", padding=12)
        resumen.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        resumen.columnconfigure(0, weight=1)
        ttk.Label(resumen, textvariable=self.estado_var, style="Metric.TLabel").grid(
            row=0,
            column=0,
            sticky=tk.W,
        )
        ttk.Label(
            resumen,
            text="Resumen del listado visible",
            style="CardText.TLabel",
        ).grid(row=1, column=0, sticky=tk.W, pady=(2, 0))

        ttk.Label(contenedor, text="Datos del cliente", style="Section.TLabel").grid(
            row=1,
            column=0,
            columnspan=2,
            sticky=tk.W,
            pady=(0, 8),
        )

        campos = [
            ("Nombre", self.nombre_var),
            ("Correo electronico", self.correo_var),
            ("Telefono", self.telefono_var),
            ("Direccion", self.direccion_var),
        ]

        for indice, (etiqueta, variable) in enumerate(campos, start=2):
            ttk.Label(contenedor, text=etiqueta).grid(
                row=indice,
                column=0,
                sticky=tk.W,
                pady=4,
            )
            ttk.Entry(contenedor, textvariable=variable).grid(
                row=indice,
                column=1,
                sticky="ew",
                pady=4,
            )

        ttk.Checkbutton(contenedor, text="Activo", variable=self.activo_var).grid(
            row=6,
            column=1,
            sticky=tk.W,
            pady=(4, 0),
        )

        botones = ttk.Frame(contenedor)
        botones.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        botones.columnconfigure(0, weight=1)
        botones.columnconfigure(1, weight=1)

        ttk.Button(
            botones,
            text="Guardar cliente",
            command=self.guardar_cliente,
            style="Primary.TButton",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Button(
            botones,
            text="Nuevo",
            command=self.limpiar_formulario,
            style="Info.TButton",
        ).grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=3)
        ttk.Button(
            botones,
            text="Eliminar",
            command=self.eliminar_cliente,
            style="Danger.TButton",
        ).grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=3)
        ttk.Button(
            botones,
            text="Actualizar lista",
            command=self.cargar_clientes,
            style="Accent.TButton",
        ).grid(row=2, column=0, columnspan=2, sticky="ew", pady=3)

    def cargar_clientes(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        clientes = self._obtener_clientes_visibles()
        for indice, cliente in enumerate(clientes):
            self.tabla.insert(
                "",
                tk.END,
                iid=str(cliente.id),
                tags=("even" if indice % 2 else "odd",),
                values=(
                    cliente.id,
                    cliente.nombre,
                    cliente.correo,
                    cliente.telefono,
                    "Activo" if cliente.activo else "Inactivo",
                ),
            )

        self.estado_var.set(f"{len(clientes)} clientes")

    def guardar_cliente(self):
        try:
            cliente = self._leer_cliente_desde_formulario()

            if self.cliente_seleccionado_id is None:
                self.clientes_controller.crear_cliente(cliente)
                mensaje = "Cliente registrado correctamente."
            else:
                self.clientes_controller.actualizar_cliente(
                    self.cliente_seleccionado_id,
                    cliente,
                )
                mensaje = "Cliente actualizado correctamente."

            self.cargar_clientes()
            self.limpiar_formulario()
            messagebox.showinfo("Clientes", mensaje)
        except Exception as error:
            messagebox.showerror("Clientes", str(error))

    def eliminar_cliente(self):
        cliente_id = self._obtener_cliente_id_seleccionado()
        if cliente_id is None:
            return

        confirmar = messagebox.askyesno(
            "Eliminar cliente",
            "Desea desactivar el cliente seleccionado?",
        )
        if not confirmar:
            return

        try:
            self.clientes_controller.eliminar_cliente(cliente_id)
            self.cargar_clientes()
            self.limpiar_formulario()
            messagebox.showinfo("Clientes", "Cliente desactivado correctamente.")
        except Exception as error:
            messagebox.showerror("Clientes", str(error))

    def limpiar_formulario(self):
        self.cliente_seleccionado_id = None
        self.nombre_var.set("")
        self.correo_var.set("")
        self.telefono_var.set("")
        self.direccion_var.set("")
        self.activo_var.set(True)
        self.tabla.selection_remove(self.tabla.selection())

    def _al_seleccionar_cliente(self, _evento):
        cliente_id = self._obtener_cliente_id_seleccionado(mostrar_error=False)
        if cliente_id is None:
            return

        cliente = self.clientes_controller.obtener_cliente(cliente_id)
        if cliente is None:
            return

        self.cliente_seleccionado_id = cliente.id
        self.nombre_var.set(cliente.nombre)
        self.correo_var.set(cliente.correo)
        self.telefono_var.set(cliente.telefono)
        self.direccion_var.set(cliente.direccion)
        self.activo_var.set(cliente.activo)

    def _leer_cliente_desde_formulario(self):
        cliente = Cliente(
            nombre=self.nombre_var.get(),
            correo=self.correo_var.get(),
            telefono=self.telefono_var.get(),
            direccion=self.direccion_var.get(),
            activo=self.activo_var.get(),
        )
        cliente.validar()
        return cliente

    def _obtener_cliente_id_seleccionado(self, mostrar_error=True):
        seleccion = self.tabla.selection()

        if not seleccion:
            if mostrar_error:
                messagebox.showwarning("Clientes", "Seleccione un cliente.")
            return None

        return int(seleccion[0])

    def _obtener_clientes_visibles(self):
        texto = self.busqueda_var.get().strip()
        if texto:
            return self.clientes_controller.buscar_clientes(texto, incluir_inactivos=True)
        return self.clientes_controller.listar_clientes(incluir_inactivos=True)

    def _limpiar_busqueda(self):
        self.busqueda_var.set("")
        self.cargar_clientes()


def abrir_clientes(root=None):
    standalone = root is None
    contenedor = root or tk.Tk()
    ventana = contenedor.winfo_toplevel()
    aplicar_tema(ventana)
    ventana.title("Perfum Lab - Clientes")
    ventana.geometry("1180x720")
    ventana.minsize(980, 620)

    vista = ClientesView(contenedor)
    vista.pack(fill=tk.BOTH, expand=True)

    if standalone:
        ventana.mainloop()

    return vista
