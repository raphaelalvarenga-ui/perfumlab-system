from app.database.json_storage import DATABASE_PATH, inicializar_datos_json


def inicializar_base_datos(ruta_db=DATABASE_PATH):
    inicializar_datos_json(ruta_db)


def obtener_conexion(ruta_db=DATABASE_PATH):
    raise RuntimeError(
        "El sistema ahora usa archivos JSON. Use app.database.json_storage "
        "para leer y guardar datos."
    )


def conectar():
    return obtener_conexion()


def crear_tablas():
    inicializar_base_datos()
