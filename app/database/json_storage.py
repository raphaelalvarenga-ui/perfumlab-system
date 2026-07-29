import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_DIR = BASE_DIR / "database"
JSON_DIR = DATABASE_DIR / "json"
DATABASE_PATH = JSON_DIR

TABLAS = {
    "usuarios": "usuarios.json",
    "clientes": "clientes.json",
    "categorias": "categorias.json",
    "productos": "productos.json",
    "movimientos_inventario": "movimientos_inventario.json",
    "ventas": "ventas.json",
    "detalle_venta": "detalle_venta.json",
    "facturas": "facturas.json",
}

FECHA_INICIAL = "2026-07-13 13:51:00"

DATOS_INICIALES = {
    "usuarios": [
        {
            "id": 1,
            "nombre": "Administrador",
            "usuario": "admin",
            "contrasena": "1234",
            "rol": "Administrador",
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        }
    ],
    "clientes": [
        {
            "id": 1,
            "nombre": "Maria Lopez",
            "telefono": "9999-1001",
            "direccion": "La Paz, Honduras",
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
        {
            "id": 2,
            "nombre": "Carlos Rivera",
            "telefono": "9999-1002",
            "direccion": "Comayagua, Honduras",
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
        {
            "id": 3,
            "nombre": "Sofia Martinez",
            "telefono": "9999-1003",
            "direccion": "Tegucigalpa, Honduras",
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
        {
            "id": 4,
            "nombre": "Hotel Brisas",
            "telefono": "9999-1004",
            "direccion": "Valle de Angeles, Honduras",
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
        {
            "id": 5,
            "nombre": "Boutique Aroma",
            "telefono": "9999-1005",
            "direccion": "San Pedro Sula, Honduras",
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
    ],
    "categorias": [
        {
            "id": 1,
            "nombre": "Hombre",
            "descripcion": "Perfumes para hombre",
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
        {
            "id": 2,
            "nombre": "Mujer",
            "descripcion": "Perfumes para mujer",
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
        {
            "id": 3,
            "nombre": "Unisex",
            "descripcion": "Fragancias unisex",
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
        {
            "id": 4,
            "nombre": "Ambientales",
            "descripcion": "Aromas para espacios y productos complementarios",
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
    ],
    "productos": [
        {
            "id": 1,
            "sku": "PF-HOM-001",
            "nombre": "Cedro Nocturno",
            "categoria_id": 1,
            "marca": "Perfum Lab",
            "descripcion": "Acordes de cedro, bergamota y ambar.",
            "costo": 420.0,
            "precio": 850.0,
            "stock_actual": 18,
            "stock_minimo": 5,
            "ml": 100,
            "imagen": None,
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
        {
            "id": 2,
            "sku": "PF-HOM-002",
            "nombre": "Vetiver Reserva",
            "categoria_id": 1,
            "marca": "Perfum Lab",
            "descripcion": "Notas frescas de vetiver, lavanda y pimienta.",
            "costo": 390.0,
            "precio": 780.0,
            "stock_actual": 4,
            "stock_minimo": 5,
            "ml": 100,
            "imagen": None,
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
        {
            "id": 3,
            "sku": "PF-HOM-003",
            "nombre": "Azul Intenso",
            "categoria_id": 1,
            "marca": "Perfum Lab",
            "descripcion": "Fragancia marina con fondo amaderado.",
            "costo": 350.0,
            "precio": 700.0,
            "stock_actual": 22,
            "stock_minimo": 6,
            "ml": 75,
            "imagen": None,
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
        {
            "id": 4,
            "sku": "PF-MUJ-001",
            "nombre": "Rosa Imperial",
            "categoria_id": 2,
            "marca": "Perfum Lab",
            "descripcion": "Rosa, vainilla suave y almizcle limpio.",
            "costo": 410.0,
            "precio": 820.0,
            "stock_actual": 15,
            "stock_minimo": 5,
            "ml": 100,
            "imagen": None,
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
        {
            "id": 5,
            "sku": "PF-MUJ-002",
            "nombre": "Vainilla Serena",
            "categoria_id": 2,
            "marca": "Perfum Lab",
            "descripcion": "Vainilla cremosa con salida de pera y jazmin.",
            "costo": 360.0,
            "precio": 720.0,
            "stock_actual": 20,
            "stock_minimo": 6,
            "ml": 75,
            "imagen": None,
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
        {
            "id": 6,
            "sku": "PF-MUJ-003",
            "nombre": "Jazmin Dorado",
            "categoria_id": 2,
            "marca": "Perfum Lab",
            "descripcion": "Jazmin blanco, flor de azahar y maderas claras.",
            "costo": 380.0,
            "precio": 760.0,
            "stock_actual": 6,
            "stock_minimo": 6,
            "ml": 50,
            "imagen": None,
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
        {
            "id": 7,
            "sku": "PF-UNI-001",
            "nombre": "Citrus Blanco",
            "categoria_id": 3,
            "marca": "Perfum Lab",
            "descripcion": "Salida citrica con te verde y musgo limpio.",
            "costo": 330.0,
            "precio": 690.0,
            "stock_actual": 25,
            "stock_minimo": 8,
            "ml": 100,
            "imagen": None,
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
        {
            "id": 8,
            "sku": "PF-UNI-002",
            "nombre": "Ambar Claro",
            "categoria_id": 3,
            "marca": "Perfum Lab",
            "descripcion": "Ambar, tonka y maderas suaves de uso diario.",
            "costo": 440.0,
            "precio": 890.0,
            "stock_actual": 12,
            "stock_minimo": 4,
            "ml": 100,
            "imagen": None,
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
        {
            "id": 9,
            "sku": "PF-UNI-003",
            "nombre": "Musk Urbano",
            "categoria_id": 3,
            "marca": "Perfum Lab",
            "descripcion": "Almizcle fresco, iris y notas limpias.",
            "costo": 310.0,
            "precio": 650.0,
            "stock_actual": 30,
            "stock_minimo": 10,
            "ml": 75,
            "imagen": None,
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
        {
            "id": 10,
            "sku": "PF-AMB-001",
            "nombre": "Bruma de Lavanda",
            "categoria_id": 4,
            "marca": "Perfum Lab Home",
            "descripcion": "Spray ambiental con lavanda y eucalipto.",
            "costo": 190.0,
            "precio": 390.0,
            "stock_actual": 16,
            "stock_minimo": 5,
            "ml": 250,
            "imagen": None,
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
        {
            "id": 11,
            "sku": "PF-AMB-002",
            "nombre": "Vela Bosque Suave",
            "categoria_id": 4,
            "marca": "Perfum Lab Home",
            "descripcion": "Vela aromatica con pino, cedro y vainilla.",
            "costo": 160.0,
            "precio": 340.0,
            "stock_actual": 9,
            "stock_minimo": 3,
            "ml": 200,
            "imagen": None,
            "activo": 1,
            "fecha_creacion": FECHA_INICIAL,
            "fecha_actualizacion": None,
        },
    ],
    "movimientos_inventario": [
        {
            "id": 1,
            "producto_id": 1,
            "tipo_movimiento": "ENTRADA",
            "cantidad": 18,
            "stock_anterior": 0,
            "stock_nuevo": 18,
            "motivo": "Carga inicial de productos",
            "fecha": FECHA_INICIAL,
        },
        {
            "id": 2,
            "producto_id": 2,
            "tipo_movimiento": "ENTRADA",
            "cantidad": 4,
            "stock_anterior": 0,
            "stock_nuevo": 4,
            "motivo": "Carga inicial de productos",
            "fecha": FECHA_INICIAL,
        },
        {
            "id": 3,
            "producto_id": 3,
            "tipo_movimiento": "ENTRADA",
            "cantidad": 22,
            "stock_anterior": 0,
            "stock_nuevo": 22,
            "motivo": "Carga inicial de productos",
            "fecha": FECHA_INICIAL,
        },
        {
            "id": 4,
            "producto_id": 4,
            "tipo_movimiento": "ENTRADA",
            "cantidad": 15,
            "stock_anterior": 0,
            "stock_nuevo": 15,
            "motivo": "Carga inicial de productos",
            "fecha": FECHA_INICIAL,
        },
        {
            "id": 5,
            "producto_id": 5,
            "tipo_movimiento": "ENTRADA",
            "cantidad": 20,
            "stock_anterior": 0,
            "stock_nuevo": 20,
            "motivo": "Carga inicial de productos",
            "fecha": FECHA_INICIAL,
        },
        {
            "id": 6,
            "producto_id": 6,
            "tipo_movimiento": "ENTRADA",
            "cantidad": 6,
            "stock_anterior": 0,
            "stock_nuevo": 6,
            "motivo": "Carga inicial de productos",
            "fecha": FECHA_INICIAL,
        },
        {
            "id": 7,
            "producto_id": 7,
            "tipo_movimiento": "ENTRADA",
            "cantidad": 25,
            "stock_anterior": 0,
            "stock_nuevo": 25,
            "motivo": "Carga inicial de productos",
            "fecha": FECHA_INICIAL,
        },
        {
            "id": 8,
            "producto_id": 8,
            "tipo_movimiento": "ENTRADA",
            "cantidad": 12,
            "stock_anterior": 0,
            "stock_nuevo": 12,
            "motivo": "Carga inicial de productos",
            "fecha": FECHA_INICIAL,
        },
        {
            "id": 9,
            "producto_id": 9,
            "tipo_movimiento": "ENTRADA",
            "cantidad": 30,
            "stock_anterior": 0,
            "stock_nuevo": 30,
            "motivo": "Carga inicial de productos",
            "fecha": FECHA_INICIAL,
        },
        {
            "id": 10,
            "producto_id": 10,
            "tipo_movimiento": "ENTRADA",
            "cantidad": 16,
            "stock_anterior": 0,
            "stock_nuevo": 16,
            "motivo": "Carga inicial de productos",
            "fecha": FECHA_INICIAL,
        },
        {
            "id": 11,
            "producto_id": 11,
            "tipo_movimiento": "ENTRADA",
            "cantidad": 9,
            "stock_anterior": 0,
            "stock_nuevo": 9,
            "motivo": "Carga inicial de productos",
            "fecha": FECHA_INICIAL,
        },
    ],
    "ventas": [],
    "detalle_venta": [],
    "facturas": [],
}


def fecha_actual():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def inicializar_datos_json(ruta_datos=JSON_DIR):
    ruta_datos = Path(ruta_datos)
    ruta_datos.mkdir(parents=True, exist_ok=True)

    for tabla in TABLAS:
        ruta_archivo = _ruta_tabla(tabla, ruta_datos)
        if not ruta_archivo.exists():
            _guardar_json(ruta_archivo, deepcopy(DATOS_INICIALES[tabla]))


def cargar_tabla(tabla, ruta_datos=JSON_DIR):
    inicializar_datos_json(ruta_datos)
    ruta_archivo = _ruta_tabla(tabla, ruta_datos)

    try:
        with open(ruta_archivo, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
    except json.JSONDecodeError as error:
        raise ValueError(f"El archivo {ruta_archivo.name} no contiene JSON valido.") from error

    if not isinstance(datos, list):
        raise ValueError(f"El archivo {ruta_archivo.name} debe contener una lista.")

    return datos


def guardar_tabla(tabla, datos, ruta_datos=JSON_DIR):
    inicializar_datos_json(ruta_datos)
    _guardar_json(_ruta_tabla(tabla, ruta_datos), datos)


def cargar_todo(ruta_datos=JSON_DIR):
    return {tabla: cargar_tabla(tabla, ruta_datos) for tabla in TABLAS}


def guardar_todo(datos_por_tabla, ruta_datos=JSON_DIR):
    inicializar_datos_json(ruta_datos)
    rutas_temporales = []

    for tabla, datos in datos_por_tabla.items():
        ruta_archivo = _ruta_tabla(tabla, ruta_datos)
        ruta_temporal = ruta_archivo.with_suffix(ruta_archivo.suffix + ".tmp")
        _guardar_json(ruta_temporal, datos)
        rutas_temporales.append((ruta_temporal, ruta_archivo))

    for ruta_temporal, ruta_archivo in rutas_temporales:
        ruta_temporal.replace(ruta_archivo)


def siguiente_id(tabla, filas=None):
    filas = filas if filas is not None else cargar_tabla(tabla)
    ids = [int(fila["id"]) for fila in filas if fila.get("id") is not None]
    return max(ids, default=0) + 1


def buscar_por_id(filas, registro_id):
    registro_id = int(registro_id)
    return next((fila for fila in filas if int(fila.get("id", 0)) == registro_id), None)


def es_activo(registro):
    return bool(registro.get("activo", 1))


def coincide_texto(valor, texto):
    return texto.lower() in str(valor or "").lower()


def _ruta_tabla(tabla, ruta_datos=JSON_DIR):
    if tabla not in TABLAS:
        raise ValueError(f"Tabla JSON no reconocida: {tabla}")

    return Path(ruta_datos) / TABLAS[tabla]


def _guardar_json(ruta_archivo, datos):
    with open(ruta_archivo, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=4, ensure_ascii=False)
        archivo.write("\n")
