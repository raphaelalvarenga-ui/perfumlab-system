import json
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

DATOS_INICIALES = {tabla: [] for tabla in TABLAS}


def fecha_actual():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def inicializar_datos_json(ruta_datos=JSON_DIR):
    ruta_datos = Path(ruta_datos)
    ruta_datos.mkdir(parents=True, exist_ok=True)

    for tabla in TABLAS:
        ruta_archivo = _ruta_tabla(tabla, ruta_datos)
        if not ruta_archivo.exists():
            _guardar_json(ruta_archivo, DATOS_INICIALES[tabla])

    _migrar_clientes(ruta_datos)


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


def _migrar_clientes(ruta_datos):
    ruta_archivo = _ruta_tabla("clientes", ruta_datos)
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as archivo:
            clientes = json.load(archivo)
    except json.JSONDecodeError as error:
        raise ValueError(f"El archivo {ruta_archivo.name} no contiene JSON valido.") from error

    if not isinstance(clientes, list):
        raise ValueError(f"El archivo {ruta_archivo.name} debe contener una lista.")

    hubo_cambios = False
    for cliente in clientes:
        if "correo" not in cliente:
            cliente["correo"] = ""
            hubo_cambios = True
        if "telefono" not in cliente:
            cliente["telefono"] = ""
            hubo_cambios = True
        if "direccion" not in cliente:
            cliente["direccion"] = ""
            hubo_cambios = True
        if "activo" not in cliente:
            cliente["activo"] = 1
            hubo_cambios = True

    if hubo_cambios:
        _guardar_json(ruta_archivo, clientes)


def _guardar_json(ruta_archivo, datos):
    with open(ruta_archivo, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=4, ensure_ascii=False)
        archivo.write("\n")
