import importlib
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ui_theme import aplicar_tema
from app.views.productos_view import abrir_productos


class PerfumLabApp:
    def __init__(self, root):
        self.root = root
        self.titulo_var = tk.StringVar(value="Inicio")

        self.root.title("Perfum Lab")
        self.root.geometry("1180x720")
        self.root.minsize(980, 620)
        aplicar_tema(self.root)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self._crear_barra_superior()
        self.contenido = ttk.Frame(self.root, padding=(18, 14, 18, 18))
        self.contenido.grid(row=1, column=0, sticky="nsew")
        self.contenido.columnconfigure(0, weight=1)
        self.contenido.rowconfigure(0, weight=1)

        self.mostrar_inicio()

    def _crear_barra_superior(self):
        barra = ttk.Frame(self.root, style="Surface.TFrame", padding=(18, 10))
        barra.grid(row=0, column=0, sticky="ew")
        barra.columnconfigure(0, weight=1)
        barra.columnconfigure(2, weight=1)

        ttk.Label(barra, textvariable=self.titulo_var, style="CardText.TLabel").grid(
            row=0,
            column=0,
            sticky=tk.W,
        )
        ttk.Label(barra, text="Perfum Lab", style="TopBrand.TLabel").grid(
            row=0,
            column=1,
            sticky=tk.N,
        )
        self.boton_inicio = ttk.Button(
            barra,
            text="Regresar al inicio",
            command=self.mostrar_inicio,
            style="Primary.TButton",
        )
        self.boton_inicio.grid(row=0, column=2, sticky=tk.E)

    def _limpiar_contenido(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()

    def mostrar_inicio(self):
        self.titulo_var.set("")
        self.boton_inicio.grid_remove()
        self.root.title("Perfum Lab - Inicio")
        self._limpiar_contenido()
        crear_menu_principal(self.contenido, self)

    def mostrar_productos(self):
        self._mostrar_modulo("Productos e inventario", lambda: abrir_productos(self.contenido))

    def mostrar_ventas(self):
        modulo_ventas = importlib.import_module("app.ventas.ventas")
        self._mostrar_modulo("Ventas", lambda: modulo_ventas.abrir_ventas(self.contenido))

    def mostrar_facturas(self):
        self._mostrar_modulo(
            "Facturas",
            lambda: abrir_modulo_si_existe(
                self.contenido,
                "Facturas",
                "app.facturas.facturas",
                ("abrir_facturas", "mostrar_facturas", "main"),
            ),
        )

    def mostrar_reportes(self):
        self._mostrar_modulo(
            "Reportes",
            lambda: abrir_modulo_si_existe(
                self.contenido,
                "Reportes",
                "app.reportes.reportes",
                ("abrir_reportes", "mostrar_reportes", "main"),
            ),
        )

    def _mostrar_modulo(self, titulo, renderizar):
        self.titulo_var.set(titulo)
        self.boton_inicio.grid()
        self.boton_inicio.state(["!disabled"])
        self._limpiar_contenido()
        renderizar()


def abrir_modulo_si_existe(master, titulo, ruta_modulo, funciones_apertura):
    try:
        modulo = importlib.import_module(ruta_modulo)
    except Exception as error:
        messagebox.showerror(titulo, f"No se pudo cargar el modulo:\n{error}")
        return

    for nombre_funcion in funciones_apertura:
        funcion = getattr(modulo, nombre_funcion, None)
        if callable(funcion):
            try:
                funcion(master)
            except TypeError:
                funcion()
            return

    frame = ttk.Frame(master, padding=18)
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text=titulo).pack(anchor=tk.W, pady=(0, 10))
    ttk.Label(
        frame,
        text=(
            "El modulo existe, pero aun no expone una ventana o funcion "
            "de apertura para conectarlo al menu principal."
        ),
        wraplength=360,
    ).pack(anchor=tk.W)


def crear_menu_principal(root, app):
    contenedor = ttk.Frame(root, padding=28)
    contenedor.grid(row=0, column=0, sticky="nsew")
    contenedor.columnconfigure(0, weight=1)
    contenedor.rowconfigure(1, weight=1)

    encabezado = ttk.Frame(contenedor)
    encabezado.grid(row=0, column=0, sticky="ew", pady=(0, 24))
    encabezado.columnconfigure(0, weight=1)

    ttk.Label(encabezado, text="Perfum Lab", style="HomeBrand.TLabel").grid(
        row=0,
        column=0,
        sticky=tk.N,
    )
    ttk.Label(
        encabezado,
        text="Inventario, ventas, facturas y reportes",
        style="HomeTagline.TLabel",
    ).grid(row=1, column=0, sticky=tk.N, pady=(4, 0))

    botones = [
        (
            "Productos e inventario",
            "Catalogo, stock y movimientos del almacen.",
            app.mostrar_productos,
            "Primary.TButton",
        ),
        (
            "Ventas",
            "Carrito, registro de ventas y anulaciones.",
            app.mostrar_ventas,
            "Primary.TButton",
        ),
        (
            "Facturas",
            "Emision, detalle y exportacion de facturas.",
            app.mostrar_facturas,
            "Primary.TButton",
        ),
        (
            "Reportes",
            "Resumen operativo y exportacion CSV.",
            app.mostrar_reportes,
            "Primary.TButton",
        ),
    ]

    modulos = ttk.Frame(contenedor, style="Surface.TFrame", padding=(18, 12))
    modulos.grid(row=1, column=0, sticky="nsew")
    modulos.columnconfigure(0, weight=1)

    for indice, (texto, descripcion, comando, estilo) in enumerate(botones):
        fila = ttk.Frame(modulos, style="Surface.TFrame", padding=(0, 10))
        fila.grid(
            row=indice,
            column=0,
            sticky="nsew",
            pady=(0, 1),
        )
        fila.columnconfigure(0, weight=1)

        ttk.Label(fila, text=texto, style="CardTitle.TLabel").grid(
            row=0,
            column=0,
            sticky=tk.W,
        )
        ttk.Label(
            fila,
            text=descripcion,
            style="CardText.TLabel",
            wraplength=420,
        ).grid(row=1, column=0, sticky=tk.W, pady=(2, 0))
        ttk.Button(fila, text="Abrir", command=comando, style=estilo).grid(
            row=0,
            column=1,
            rowspan=2,
            sticky=tk.E,
            padx=(18, 0),
            ipadx=12,
        )


def main():
    root = tk.Tk()
    PerfumLabApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
