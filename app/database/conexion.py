import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "perfumlab.sqlite3"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"


def obtener_conexion(ruta_db=DATABASE_PATH):
    conexion = sqlite3.connect(ruta_db)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def inicializar_base_datos(ruta_db=DATABASE_PATH):
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    with obtener_conexion(ruta_db) as conexion:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as archivo_schema:
            conexion.executescript(archivo_schema.read())
        conexion.commit()


def conectar():
    return obtener_conexion()


def crear_tablas():
    inicializar_base_datos()