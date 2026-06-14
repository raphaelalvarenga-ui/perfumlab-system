from app.database.conexion import DATABASE_PATH, inicializar_base_datos, obtener_conexion


class InventarioController:
    def __init__(self, ruta_db=DATABASE_PATH):
        self.ruta_db = ruta_db
        inicializar_base_datos(self.ruta_db)

    def registrar_entrada(self, producto_id, cantidad, motivo):
        self._validar_cantidad(cantidad)

        with obtener_conexion(self.ruta_db) as conexion:
            stock_anterior = self._obtener_stock_actual(conexion, producto_id)
            stock_nuevo = stock_anterior + cantidad
            self._actualizar_stock(conexion, producto_id, stock_nuevo)
            movimiento_id = self._registrar_movimiento(
                conexion,
                producto_id,
                "ENTRADA",
                cantidad,
                stock_anterior,
                stock_nuevo,
                motivo,
            )
            conexion.commit()
            return movimiento_id

    def registrar_salida(self, producto_id, cantidad, motivo):
        self._validar_cantidad(cantidad)

        with obtener_conexion(self.ruta_db) as conexion:
            stock_anterior = self._obtener_stock_actual(conexion, producto_id)

            if cantidad > stock_anterior:
                raise ValueError("No hay stock suficiente para registrar la salida.")

            stock_nuevo = stock_anterior - cantidad
            self._actualizar_stock(conexion, producto_id, stock_nuevo)
            movimiento_id = self._registrar_movimiento(
                conexion,
                producto_id,
                "SALIDA",
                cantidad,
                stock_anterior,
                stock_nuevo,
                motivo,
            )
            conexion.commit()
            return movimiento_id

    def registrar_ajuste(self, producto_id, nuevo_stock, motivo):
        if nuevo_stock < 0:
            raise ValueError("El nuevo stock no puede ser negativo.")

        with obtener_conexion(self.ruta_db) as conexion:
            stock_anterior = self._obtener_stock_actual(conexion, producto_id)
            cantidad = abs(nuevo_stock - stock_anterior)

            if cantidad <= 0:
                raise ValueError("El ajuste debe cambiar el stock actual.")

            self._actualizar_stock(conexion, producto_id, nuevo_stock)
            movimiento_id = self._registrar_movimiento(
                conexion,
                producto_id,
                "AJUSTE",
                cantidad,
                stock_anterior,
                nuevo_stock,
                motivo,
            )
            conexion.commit()
            return movimiento_id

    def obtener_movimientos(self):
        with obtener_conexion(self.ruta_db) as conexion:
            filas = conexion.execute(
                """
                SELECT
                    id,
                    producto_id,
                    tipo_movimiento,
                    cantidad,
                    stock_anterior,
                    stock_nuevo,
                    motivo,
                    fecha
                FROM movimientos_inventario
                ORDER BY fecha DESC, id DESC
                """
            ).fetchall()

        return [dict(fila) for fila in filas]

    def _validar_cantidad(self, cantidad):
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero.")

    def _obtener_stock_actual(self, conexion, producto_id):
        fila = conexion.execute(
            "SELECT stock_actual FROM productos WHERE id = ?",
            (producto_id,),
        ).fetchone()

        if fila is None:
            raise ValueError("El producto indicado no existe.")

        return int(fila["stock_actual"])

    def _actualizar_stock(self, conexion, producto_id, stock_nuevo):
        conexion.execute(
            """
            UPDATE productos
            SET stock_actual = ?, fecha_actualizacion = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (stock_nuevo, producto_id),
        )

    def _registrar_movimiento(
        self,
        conexion,
        producto_id,
        tipo_movimiento,
        cantidad,
        stock_anterior,
        stock_nuevo,
        motivo,
    ):
        cursor = conexion.execute(
            """
            INSERT INTO movimientos_inventario (
                producto_id,
                tipo_movimiento,
                cantidad,
                stock_anterior,
                stock_nuevo,
                motivo
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                producto_id,
                tipo_movimiento,
                cantidad,
                stock_anterior,
                stock_nuevo,
                motivo.strip() if motivo else "",
            ),
        )
        return cursor.lastrowid
