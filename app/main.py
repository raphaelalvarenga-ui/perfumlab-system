import importlib
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.api_client import get_api_client, reset_api_client
from app.api_client.session import get_user_session
from app.core.config import get_settings
from app.ui_theme import aplicar_tema
from app.views.clientes_view import abrir_clientes
from app.views.productos_view import abrir_productos


class PerfumLabApp:
    def __init__(self, root):
        self.root = root
        self.session = get_user_session()
        self.api = get_api_client()
        self.api.on_authentication_error = self._manejar_sesion_expirada
        self.titulo_var = tk.StringVar(value="Inicio")
        self.usuario_var = tk.StringVar()

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
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)

        self._actualizar_usuario()
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
        usuario_frame = ttk.Frame(barra, style="Surface.TFrame")
        usuario_frame.grid(row=0, column=2, sticky=tk.E)
        ttk.Label(
            usuario_frame,
            textvariable=self.usuario_var,
            style="CardText.TLabel",
        ).grid(row=0, column=0, sticky=tk.E, padx=(0, 10))
        self.boton_logout = ttk.Button(
            usuario_frame,
            text="Cerrar sesion",
            command=self.cerrar_sesion,
            style="Warning.TButton",
        )
        self.boton_logout.grid(row=0, column=1, sticky=tk.E, padx=(0, 10))
        self.boton_inicio = ttk.Button(
            usuario_frame,
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

    def mostrar_clientes(self):
        self._mostrar_modulo("Clientes", lambda: abrir_clientes(self.contenido))

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
        if not self.session.is_admin:
            messagebox.showerror(
                "Reportes",
                "No tiene permisos para acceder a reportes.",
            )
            return
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
        try:
            renderizar()
        except Exception as error:
            messagebox.showerror(titulo, str(error))

    def cerrar_sesion(self):
        get_user_session().clear()
        reset_api_client()
        self.root.withdraw()
        self._limpiar_contenido()
        if mostrar_login(self.root):
            self.session = get_user_session()
            self.api = get_api_client()
            self.api.on_authentication_error = self._manejar_sesion_expirada
            self._actualizar_usuario()
            self.root.deiconify()
            self.mostrar_inicio()
        else:
            self.cerrar()

    def cerrar(self):
        get_user_session().clear()
        reset_api_client()
        self.root.destroy()

    def _actualizar_usuario(self):
        nombre = self.session.nombre or self.session.username
        self.usuario_var.set(f"{nombre} - {self.session.rol}")

    def _manejar_sesion_expirada(self, error):
        if not self.root.winfo_exists():
            return
        self.root.after(0, lambda: self._cerrar_sesion_expirada(error))

    def _cerrar_sesion_expirada(self, error):
        if not self.root.winfo_exists():
            return
        messagebox.showerror("Sesion", str(error))
        self.cerrar_sesion()


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
            except Exception as error:
                messagebox.showerror(titulo, str(error))
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
            "Clientes",
            "Correos, telefonos y estado de clientes.",
            app.mostrar_clientes,
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
    ]

    if get_user_session().is_admin:
        botones.append(
            (
                "Reportes",
                "Resumen operativo y exportacion CSV.",
                app.mostrar_reportes,
                "Primary.TButton",
            )
        )

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
    root.withdraw()
    aplicar_tema(root)

    try:
        verificar_api_disponible()
    except Exception as error:
        settings = get_settings()
        messagebox.showerror(
            "Perfum Lab API",
            "No se pudo conectar con Perfum Lab API.\n\n"
            "Verifique que el servidor este iniciado.\n\n"
            f"URL: {settings.perfumlab_api_url}\n"
            f"Detalle: {error}",
        )
        reset_api_client()
        root.destroy()
        return

    if not mostrar_login(root):
        reset_api_client()
        root.destroy()
        return

    root.deiconify()
    PerfumLabApp(root)
    root.mainloop()


def verificar_api_disponible():
    get_api_client().health_check(include_db=True)


def mostrar_login(root):
    resultado = {"ok": False}
    usuario_var = tk.StringVar()
    password_var = tk.StringVar()
    mensaje_var = tk.StringVar()

    dialogo = tk.Toplevel(root)
    dialogo.title("Perfum Lab - Iniciar sesion")
    dialogo.resizable(False, False)
    dialogo.transient(root)
    dialogo.grab_set()
    aplicar_tema(dialogo)

    frame = ttk.Frame(dialogo, padding=20)
    frame.grid(row=0, column=0, sticky="nsew")
    frame.columnconfigure(1, weight=1)

    ttk.Label(frame, text="Perfum Lab", style="Section.TLabel").grid(
        row=0,
        column=0,
        columnspan=2,
        sticky=tk.W,
        pady=(0, 12),
    )
    ttk.Label(frame, text="Usuario").grid(row=1, column=0, sticky=tk.W, pady=4)
    usuario_entry = ttk.Entry(frame, textvariable=usuario_var, width=32)
    usuario_entry.grid(row=1, column=1, sticky="ew", pady=4)

    ttk.Label(frame, text="Contrasena").grid(row=2, column=0, sticky=tk.W, pady=4)
    password_entry = ttk.Entry(frame, textvariable=password_var, show="*", width=32)
    password_entry.grid(row=2, column=1, sticky="ew", pady=4)

    ttk.Label(
        frame,
        textvariable=mensaje_var,
        foreground="#B42318",
        wraplength=320,
    ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(6, 2))

    def cancelar():
        resultado["ok"] = False
        dialogo.destroy()

    def iniciar_sesion(_evento=None):
        usuario = usuario_var.get().strip()
        password = password_var.get()

        if not usuario or not password:
            mensaje_var.set("Ingrese usuario y contrasena.")
            return

        boton_login.state(["disabled"])
        dialogo.configure(cursor="watch")
        dialogo.update_idletasks()
        try:
            get_api_client().auth.login(usuario, password)
        except Exception as error:
            mensaje_var.set(str(error))
            password_var.set("")
            password_entry.focus_set()
        else:
            resultado["ok"] = True
            dialogo.destroy()
            return
        finally:
            if dialogo.winfo_exists():
                dialogo.configure(cursor="")
                boton_login.state(["!disabled"])

    acciones = ttk.Frame(frame)
    acciones.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0))
    acciones.columnconfigure(0, weight=1)

    ttk.Button(
        acciones,
        text="Cancelar",
        command=cancelar,
        style="Info.TButton",
    ).grid(row=0, column=0, sticky=tk.W)
    boton_login = ttk.Button(
        acciones,
        text="Iniciar sesion",
        command=iniciar_sesion,
        style="Primary.TButton",
    )
    boton_login.grid(row=0, column=1, sticky=tk.E)

    dialogo.protocol("WM_DELETE_WINDOW", cancelar)
    dialogo.bind("<Return>", iniciar_sesion)
    usuario_entry.focus_set()
    dialogo.wait_window()
    return resultado["ok"]


if __name__ == "__main__":
    main()
