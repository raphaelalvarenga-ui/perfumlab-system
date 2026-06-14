import sqlite3
from pathlib import Path


class ConexionSQLite:
    def __init__(self, ruta_db):
        self.ruta_db = ruta_db
        self.conexion = None

    def __enter__(self):
        self.conexion = sqlite3.connect(self.ruta_db)
        self.conexion.row_factory = sqlite3.Row
        self.conexion.execute("PRAGMA foreign_keys = ON")
        return self.conexion

    def __exit__(self, tipo_error, valor_error, traceback):
        try:
            if tipo_error:
                self.conexion.rollback()
            else:
                self.conexion.commit()
        finally:
            self.conexion.close()


BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "perfumlab.sqlite3"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"


def obtener_conexion(ruta_db=DATABASE_PATH):
    return ConexionSQLite(ruta_db)


def inicializar_base_datos(ruta_db=DATABASE_PATH):
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    with obtener_conexion(ruta_db) as conexion:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as archivo_schema:
            conexion.executescript(archivo_schema.read())
        conexion.commit()
