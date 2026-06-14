CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    usuario TEXT NOT NULL UNIQUE,
    contrasena TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'Empleado',
    activo INTEGER NOT NULL DEFAULT 1,
    fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TEXT
);

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    telefono TEXT,
    direccion TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TEXT
);

CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TEXT
);

CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    categoria_id INTEGER,
    marca TEXT,
    descripcion TEXT,
    costo REAL NOT NULL DEFAULT 0,
    precio REAL NOT NULL DEFAULT 0,
    stock_actual INTEGER NOT NULL DEFAULT 0,
    stock_minimo INTEGER NOT NULL DEFAULT 0,
    ml INTEGER NOT NULL DEFAULT 50,
    imagen TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TEXT,
    FOREIGN KEY (categoria_id) REFERENCES categorias (id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CHECK (costo >= 0),
    CHECK (precio >= 0),
    CHECK (stock_actual >= 0),
    CHECK (stock_minimo >= 0),
    CHECK (ml > 0)
);

CREATE TABLE IF NOT EXISTS movimientos_inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    tipo_movimiento TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    stock_anterior INTEGER NOT NULL,
    stock_nuevo INTEGER NOT NULL,
    motivo TEXT,
    fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CHECK (tipo_movimiento IN ('ENTRADA', 'SALIDA', 'AJUSTE')),
    CHECK (cantidad > 0),
    CHECK (stock_anterior >= 0),
    CHECK (stock_nuevo >= 0)
);

CREATE TABLE IF NOT EXISTS ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,
    usuario_id INTEGER,
    fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total REAL NOT NULL DEFAULT 0,
    estado TEXT NOT NULL DEFAULT 'Completada',
    FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CHECK (total >= 0)
);

CREATE TABLE IF NOT EXISTS detalle_venta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario REAL NOT NULL,
    subtotal REAL NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES ventas (id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CHECK (cantidad > 0),
    CHECK (precio_unitario >= 0),
    CHECK (subtotal >= 0)
);

CREATE TABLE IF NOT EXISTS facturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER NOT NULL UNIQUE,
    numero_factura TEXT NOT NULL UNIQUE,
    fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total REAL NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES ventas (id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CHECK (total >= 0)
);

INSERT OR IGNORE INTO categorias (id, nombre, descripcion) VALUES
(1, 'Hombre', 'Perfumes para hombre'),
(2, 'Mujer', 'Perfumes para mujer');

INSERT OR IGNORE INTO usuarios (id, nombre, usuario, contrasena, rol) VALUES
(1, 'Administrador', 'admin', '1234', 'Administrador');
