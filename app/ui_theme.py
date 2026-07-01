import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk


COLORS = {
    "background": "#f7f8fa",
    "surface": "#ffffff",
    "surface_alt": "#eef2f7",
    "border": "#d9dee7",
    "text": "#111827",
    "muted": "#6b7280",
    "primary": "#2563eb",
    "primary_dark": "#1d4ed8",
    "accent": "#0f766e",
    "info": "#7c3aed",
    "info_dark": "#6d28d9",
    "secondary": "#475569",
    "secondary_dark": "#334155",
    "warning_button": "#f97316",
    "warning_button_dark": "#ea580c",
    "danger": "#dc2626",
    "warning": "#92400e",
    "table_alt": "#f9fafb",
    "table_low": "#fff7ed",
}


def obtener_ruta_recurso(*partes):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base.joinpath(*partes)


def aplicar_icono(root):
    icono_ico = obtener_ruta_recurso("assets", "logo", "logoperfumlab-window.ico")
    icono_png = obtener_ruta_recurso("assets", "logo", "logoperfumlab-window.png")

    if icono_ico.exists():
        try:
            root.iconbitmap(str(icono_ico))
        except tk.TclError:
            pass

    if icono_png.exists():
        try:
            icono = tk.PhotoImage(file=str(icono_png))
            root.iconphoto(True, icono)
            root._perfumlab_icono = icono
        except tk.TclError:
            pass


def aplicar_tema(root):
    aplicar_icono(root)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.configure(bg=COLORS["background"])

    style.configure(
        ".",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=("Segoe UI", 9),
    )
    style.configure("TFrame", background=COLORS["background"])
    style.configure("Surface.TFrame", background=COLORS["surface"])
    style.configure("Toolbar.TFrame", background=COLORS["surface_alt"])
    style.configure(
        "Toolbar.TLabel",
        background=COLORS["surface_alt"],
        foreground=COLORS["text"],
    )

    style.configure(
        "Title.TLabel",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=("Segoe UI Semibold", 18),
    )
    style.configure(
        "HomeBrand.TLabel",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=("Segoe UI Semibold", 28),
    )
    style.configure(
        "HomeTagline.TLabel",
        background=COLORS["background"],
        foreground=COLORS["muted"],
        font=("Segoe UI", 10),
    )
    style.configure(
        "TopBrand.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        font=("Segoe UI Semibold", 13),
    )
    style.configure(
        "Subtitle.TLabel",
        background=COLORS["background"],
        foreground=COLORS["muted"],
        font=("Segoe UI", 9),
    )
    style.configure(
        "Section.TLabel",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=("Segoe UI Semibold", 10),
    )
    style.configure(
        "Muted.TLabel",
        background=COLORS["background"],
        foreground=COLORS["muted"],
    )
    style.configure(
        "CardTitle.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        font=("Segoe UI Semibold", 11),
    )
    style.configure(
        "CardText.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["muted"],
    )
    style.configure(
        "Metric.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["primary_dark"],
        font=("Segoe UI Semibold", 12),
    )

    style.configure(
        "TButton",
        padding=(12, 6),
        borderwidth=1,
        focusthickness=1,
        background=COLORS["secondary"],
        foreground="#ffffff",
        bordercolor=COLORS["secondary"],
        relief=tk.FLAT,
        font=("Segoe UI Semibold", 9),
    )
    style.map(
        "TButton",
        background=[
            ("active", COLORS["secondary_dark"]),
            ("pressed", COLORS["secondary_dark"]),
        ],
        foreground=[("active", "#ffffff"), ("pressed", "#ffffff"), ("disabled", COLORS["muted"])],
    )
    style.configure(
        "Info.TButton",
        background=COLORS["info"],
        foreground="#ffffff",
        bordercolor=COLORS["info"],
        font=("Segoe UI Semibold", 9),
    )
    style.map(
        "Info.TButton",
        background=[("active", COLORS["info_dark"]), ("pressed", COLORS["info_dark"])],
        foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
    )
    style.configure(
        "Warning.TButton",
        background=COLORS["warning_button"],
        foreground="#ffffff",
        bordercolor=COLORS["warning_button"],
        font=("Segoe UI Semibold", 9),
    )
    style.map(
        "Warning.TButton",
        background=[
            ("active", COLORS["warning_button_dark"]),
            ("pressed", COLORS["warning_button_dark"]),
        ],
        foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
    )
    style.configure(
        "Secondary.TButton",
        background=COLORS["secondary"],
        foreground="#ffffff",
        bordercolor=COLORS["secondary"],
        font=("Segoe UI Semibold", 9),
    )
    style.map(
        "Secondary.TButton",
        background=[
            ("active", COLORS["secondary_dark"]),
            ("pressed", COLORS["secondary_dark"]),
        ],
        foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
    )
    style.configure(
        "Quiet.TButton",
        background=COLORS["secondary"],
        foreground="#ffffff",
        bordercolor=COLORS["secondary"],
        font=("Segoe UI Semibold", 9),
    )
    style.map(
        "Quiet.TButton",
        background=[
            ("active", COLORS["secondary_dark"]),
            ("pressed", COLORS["secondary_dark"]),
        ],
        foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
    )
    style.configure(
        "Primary.TButton",
        background=COLORS["primary"],
        foreground="#ffffff",
        bordercolor=COLORS["primary"],
        font=("Segoe UI Semibold", 9),
    )
    style.map(
        "Primary.TButton",
        background=[("active", COLORS["primary_dark"]), ("pressed", COLORS["primary_dark"])],
        foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
    )
    style.configure(
        "Accent.TButton",
        background=COLORS["accent"],
        foreground="#ffffff",
        bordercolor=COLORS["accent"],
        font=("Segoe UI Semibold", 9),
    )
    style.map(
        "Accent.TButton",
        background=[("active", "#275d57"), ("pressed", "#275d57")],
        foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
    )
    style.configure(
        "Danger.TButton",
        background=COLORS["danger"],
        foreground="#ffffff",
        bordercolor=COLORS["danger"],
        font=("Segoe UI Semibold", 9),
    )
    style.map(
        "Danger.TButton",
        background=[("active", "#b91c1c"), ("pressed", "#b91c1c")],
        foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
    )
    style.configure(
        "TEntry",
        fieldbackground="#ffffff",
        bordercolor=COLORS["border"],
        lightcolor=COLORS["border"],
        darkcolor=COLORS["border"],
        padding=(7, 5),
    )
    style.configure(
        "TCombobox",
        fieldbackground="#ffffff",
        bordercolor=COLORS["border"],
        padding=(6, 5),
    )
    style.configure(
        "Treeview",
        background="#ffffff",
        fieldbackground="#ffffff",
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        rowheight=27,
    )
    style.configure(
        "Treeview.Heading",
        background=COLORS["surface_alt"],
        foreground=COLORS["text"],
        font=("Segoe UI Semibold", 10),
        padding=(7, 6),
    )
    style.map(
        "Treeview",
        background=[("selected", COLORS["primary"])],
        foreground=[("selected", "#ffffff")],
    )
    style.configure(
        "TLabelframe",
        background=COLORS["background"],
        bordercolor=COLORS["border"],
    )
    style.configure(
        "TLabelframe.Label",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=("Segoe UI Semibold", 10),
    )
    style.configure("TNotebook", background=COLORS["background"], borderwidth=0)
    style.configure(
        "TNotebook.Tab",
        padding=(14, 7),
        background=COLORS["surface_alt"],
        foreground=COLORS["muted"],
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", COLORS["surface"])],
        foreground=[("selected", COLORS["text"])],
    )


def crear_encabezado(parent, titulo, subtitulo=None, row=0):
    encabezado = ttk.Frame(parent)
    encabezado.grid(row=row, column=0, sticky="ew", pady=(0, 14))
    encabezado.columnconfigure(0, weight=1)

    ttk.Label(encabezado, text=titulo, style="Title.TLabel").grid(
        row=0,
        column=0,
        sticky=tk.W,
    )
    if subtitulo:
        ttk.Label(encabezado, text=subtitulo, style="Subtitle.TLabel").grid(
            row=1,
            column=0,
            sticky=tk.W,
            pady=(2, 0),
        )

    return encabezado


def configurar_tabla(tabla):
    tabla.tag_configure("odd", background="#ffffff")
    tabla.tag_configure("even", background=COLORS["table_alt"])
    tabla.tag_configure("low_stock", background=COLORS["table_low"], foreground=COLORS["warning"])
