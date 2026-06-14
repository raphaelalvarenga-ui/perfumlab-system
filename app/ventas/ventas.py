from app.database.conexion import conectar


def crear_tabla_ventas():
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER NOT NULL,
        cliente TEXT NOT NULL,
        cantidad INTEGER NOT NULL,
        precio_unitario REAL NOT NULL,
        total REAL NOT NULL,
        fecha TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (producto_id) REFERENCES productos(id)
    )
    """)

    conexion.commit()
    conexion.close()


def registrar_venta(producto_id, cliente, cantidad):
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute(
        "SELECT id, nombre, precio, stock FROM productos WHERE id = ?",
        (producto_id,)
    )

    producto = cursor.fetchone()

    if producto is None:
        conexion.close()
        return False, "El producto no existe."

    precio = producto["precio"]
    stock = producto["stock"]

    if cantidad <= 0:
        conexion.close()
        return False, "La cantidad debe ser mayor que cero."

    if cantidad > stock:
        conexion.close()
        return False, "No hay suficiente stock disponible."

    total = precio * cantidad
    nuevo_stock = stock - cantidad

    cursor.execute("""
    INSERT INTO ventas (
        producto_id,
        cliente,
        cantidad,
        precio_unitario,
        total
    )
    VALUES (?, ?, ?, ?, ?)
    """, (producto_id, cliente, cantidad, precio, total))

    cursor.execute(
        "UPDATE productos SET stock = ? WHERE id = ?",
        (nuevo_stock, producto_id)
    )

    conexion.commit()
    conexion.close()

    return True, f"Venta registrada correctamente. Total: L {total:.2f}"


def obtener_ventas():
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
    SELECT 
        ventas.id,
        productos.nombre AS producto,
        ventas.cliente,
        ventas.cantidad,
        ventas.precio_unitario,
        ventas.total,
        ventas.fecha
    FROM ventas
    INNER JOIN productos ON ventas.producto_id = productos.id
    ORDER BY ventas.id DESC
    """)

    ventas = cursor.fetchall()
    conexion.close()

    return ventas


def buscar_venta_por_id(venta_id):
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
    SELECT 
        ventas.id,
        productos.nombre AS producto,
        ventas.cliente,
        ventas.cantidad,
        ventas.precio_unitario,
        ventas.total,
        ventas.fecha
    FROM ventas
    INNER JOIN productos ON ventas.producto_id = productos.id
    WHERE ventas.id = ?
    """, (venta_id,))

    venta = cursor.fetchone()
    conexion.close()

    return venta