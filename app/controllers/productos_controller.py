from app.database.conexion import DATABASE_PATH, inicializar_base_datos, obtener_conexion
from app.models.categoria import Categoria
from app.models.producto import Producto


class ProductosController:
    def __init__(self, ruta_db=DATABASE_PATH):
        self.ruta_db = ruta_db
        inicializar_base_datos(self.ruta_db)

    def crear_categoria(self, categoria):
        categoria.validar()

        with obtener_conexion(self.ruta_db) as conexion:
            cursor = conexion.execute(
                """
                INSERT INTO categorias (nombre, descripcion, activo)
                VALUES (?, ?, ?)
                """,
                (
                    categoria.nombre.strip(),
                    categoria.descripcion.strip(),
                    int(categoria.activo),
                ),
            )
            conexion.commit()
            return cursor.lastrowid

    def listar_categorias(self, incluir_inactivas=False):
        consulta = "SELECT * FROM categorias"
        parametros = []

        if not incluir_inactivas:
            consulta += " WHERE activo = ?"
            parametros.append(1)

        consulta += " ORDER BY nombre ASC"

        with obtener_conexion(self.ruta_db) as conexion:
            filas = conexion.execute(consulta, parametros).fetchall()
            return [Categoria.desde_fila(fila) for fila in filas]

    def crear_producto(self, producto):
        producto.validar()

        with obtener_conexion(self.ruta_db) as conexion:
            cursor = conexion.execute(
                """
                INSERT INTO productos (
                    sku, nombre, categoria_id, marca, descripcion,
                    costo, precio, stock_actual, stock_minimo, activo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._valores_producto(producto),
            )
            conexion.commit()
            return cursor.lastrowid

    def obtener_producto(self, producto_id):
        with obtener_conexion(self.ruta_db) as conexion:
            fila = conexion.execute(
                "SELECT * FROM productos WHERE id = ?",
                (producto_id,),
            ).fetchone()

        return Producto.desde_fila(fila) if fila else None

    def listar_productos(self, incluir_inactivos=False):
        consulta = "SELECT * FROM productos"
        parametros = []

        if not incluir_inactivos:
            consulta += " WHERE activo = ?"
            parametros.append(1)

        consulta += " ORDER BY nombre ASC"

        with obtener_conexion(self.ruta_db) as conexion:
            filas = conexion.execute(consulta, parametros).fetchall()
            return [Producto.desde_fila(fila) for fila in filas]

    def buscar_productos(self, texto, incluir_inactivos=False):
        texto_busqueda = f"%{texto.strip()}%"
        consulta = """
            SELECT * FROM productos
            WHERE (sku LIKE ? OR nombre LIKE ? OR marca LIKE ?)
        """
        parametros = [texto_busqueda, texto_busqueda, texto_busqueda]

        if not incluir_inactivos:
            consulta += " AND activo = ?"
            parametros.append(1)

        consulta += " ORDER BY nombre ASC"

        with obtener_conexion(self.ruta_db) as conexion:
            filas = conexion.execute(consulta, parametros).fetchall()
            return [Producto.desde_fila(fila) for fila in filas]

    def actualizar_producto(self, producto_id, producto):
        producto.validar()

        with obtener_conexion(self.ruta_db) as conexion:
            cursor = conexion.execute(
                """
                UPDATE productos
                SET
                    sku = ?,
                    nombre = ?,
                    categoria_id = ?,
                    marca = ?,
                    descripcion = ?,
                    costo = ?,
                    precio = ?,
                    stock_actual = ?,
                    stock_minimo = ?,
                    activo = ?,
                    fecha_actualizacion = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (*self._valores_producto(producto), producto_id),
            )
            conexion.commit()
            return cursor.rowcount > 0

    def eliminar_producto(self, producto_id):
        with obtener_conexion(self.ruta_db) as conexion:
            cursor = conexion.execute(
                """
                UPDATE productos
                SET activo = 0, fecha_actualizacion = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (producto_id,),
            )
            conexion.commit()
            return cursor.rowcount > 0

    def eliminar_producto_permanente(self, producto_id):
        with obtener_conexion(self.ruta_db) as conexion:
            cursor = conexion.execute(
                "DELETE FROM productos WHERE id = ?",
                (producto_id,),
            )
            conexion.commit()
            return cursor.rowcount > 0

    def _valores_producto(self, producto):
        return (
            producto.sku.strip(),
            producto.nombre.strip(),
            producto.categoria_id,
            producto.marca.strip(),
            producto.descripcion.strip(),
            producto.costo,
            producto.precio,
            producto.stock_actual,
            producto.stock_minimo,
            int(producto.activo),
        )
