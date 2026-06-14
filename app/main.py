import importlib
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.views.productos_view import abrir_productos


def abrir_ventana_productos(master):
    ventana = tk.Toplevel(master)
    abrir_productos(ventana)


def abrir_ventana_ventas(master):
    ventana = tk.Toplevel(master)
    modulo_ventas = importlib.import_module("app.ventas.ventas")
    modulo_ventas.abrir_ventas(ventana)


def abrir_modulo_si_existe(master, titulo, ruta_modulo, funciones_apertura):
    try:
        modulo = importlib.import_module(ruta_modulo)
    except Exception as error:
        messagebox.showerror(titulo, f"No se pudo cargar el modulo:\n{error}")
        return

    for nombre_funcion in funciones_apertura:
        funcion = getattr(modulo, nombre_funcion, None)
        if callable(funcion):
            ventana = tk.Toplevel(master)
            try:
                funcion(ventana)
            except TypeError:
                ventana.destroy()
                funcion()
            return

    ventana = tk.Toplevel(master)
    ventana.title(titulo)
    ventana.geometry("420x180")

    frame = ttk.Frame(ventana, padding=18)
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


def crear_menu_principal(root):
    root.title("Perfum Lab - Menu principal")
    root.geometry("420x300")
    root.minsize(360, 260)

    contenedor = ttk.Frame(root, padding=20)
    contenedor.pack(fill=tk.BOTH, expand=True)
    contenedor.columnconfigure(0, weight=1)

    ttk.Label(contenedor, text="Perfum Lab").grid(
        row=0,
        column=0,
        sticky=tk.W,
        pady=(0, 4),
    )
    ttk.Label(contenedor, text="Menu principal").grid(
        row=1,
        column=0,
        sticky=tk.W,
        pady=(0, 16),
    )

    botones = [
        ("Productos e inventario", lambda: abrir_ventana_productos(root)),
        ("Ventas", lambda: abrir_ventana_ventas(root)),
        (
            "Facturas",
            lambda: abrir_modulo_si_existe(
                root,
                "Facturas",
                "app.facturas.facturas",
                ("abrir_facturas", "mostrar_facturas", "main"),
            ),
        ),
        (
            "Reportes",
            lambda: abrir_modulo_si_existe(
                root,
                "Reportes",
                "app.reportes.reportes",
                ("abrir_reportes", "mostrar_reportes", "main"),
            ),
        ),
    ]

    for indice, (texto, comando) in enumerate(botones, start=2):
        ttk.Button(contenedor, text=texto, command=comando).grid(
            row=indice,
            column=0,
            sticky="ew",
            pady=5,
        )


def main():
    root = tk.Tk()
    crear_menu_principal(root)
    root.mainloop()


if __name__ == "__main__":
    main()
