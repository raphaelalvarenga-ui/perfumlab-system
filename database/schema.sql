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

INSERT OR IGNORE INTO categorias (nombre, descripcion) VALUES
('Unisex', 'Fragancias unisex'),
('Ambientales', 'Aromas para espacios y productos complementarios');

INSERT OR IGNORE INTO usuarios (id, nombre, usuario, contrasena, rol) VALUES
(1, 'Administrador', 'admin', '1234', 'Administrador');

INSERT INTO clientes (nombre, telefono, direccion)
SELECT 'Maria Lopez', '9999-1001', 'La Paz, Honduras'
WHERE NOT EXISTS (SELECT 1 FROM clientes WHERE LOWER(nombre) = LOWER('Maria Lopez'));

INSERT INTO clientes (nombre, telefono, direccion)
SELECT 'Carlos Rivera', '9999-1002', 'Comayagua, Honduras'
WHERE NOT EXISTS (SELECT 1 FROM clientes WHERE LOWER(nombre) = LOWER('Carlos Rivera'));

INSERT INTO clientes (nombre, telefono, direccion)
SELECT 'Sofia Martinez', '9999-1003', 'Tegucigalpa, Honduras'
WHERE NOT EXISTS (SELECT 1 FROM clientes WHERE LOWER(nombre) = LOWER('Sofia Martinez'));

INSERT INTO clientes (nombre, telefono, direccion)
SELECT 'Hotel Brisas', '9999-1004', 'Valle de Angeles, Honduras'
WHERE NOT EXISTS (SELECT 1 FROM clientes WHERE LOWER(nombre) = LOWER('Hotel Brisas'));

INSERT INTO clientes (nombre, telefono, direccion)
SELECT 'Boutique Aroma', '9999-1005', 'San Pedro Sula, Honduras'
WHERE NOT EXISTS (SELECT 1 FROM clientes WHERE LOWER(nombre) = LOWER('Boutique Aroma'));

INSERT OR IGNORE INTO productos (
    sku, nombre, categoria_id, marca, descripcion,
    costo, precio, stock_actual, stock_minimo, ml
) VALUES
(
    'PF-HOM-001',
    'Cedro Nocturno',
    (SELECT id FROM categorias WHERE nombre = 'Hombre'),
    'Perfum Lab',
    'Acordes de cedro, bergamota y ambar.',
    420, 850, 18, 5, 100
),
(
    'PF-HOM-002',
    'Vetiver Reserva',
    (SELECT id FROM categorias WHERE nombre = 'Hombre'),
    'Perfum Lab',
    'Notas frescas de vetiver, lavanda y pimienta.',
    390, 780, 4, 5, 100
),
(
    'PF-HOM-003',
    'Azul Intenso',
    (SELECT id FROM categorias WHERE nombre = 'Hombre'),
    'Perfum Lab',
    'Fragancia marina con fondo amaderado.',
    350, 700, 22, 6, 75
),
(
    'PF-MUJ-001',
    'Rosa Imperial',
    (SELECT id FROM categorias WHERE nombre = 'Mujer'),
    'Perfum Lab',
    'Rosa, vainilla suave y almizcle limpio.',
    410, 820, 15, 5, 100
),
(
    'PF-MUJ-002',
    'Vainilla Serena',
    (SELECT id FROM categorias WHERE nombre = 'Mujer'),
    'Perfum Lab',
    'Vainilla cremosa con salida de pera y jazmin.',
    360, 720, 20, 6, 75
),
(
    'PF-MUJ-003',
    'Jazmin Dorado',
    (SELECT id FROM categorias WHERE nombre = 'Mujer'),
    'Perfum Lab',
    'Jazmin blanco, flor de azahar y maderas claras.',
    380, 760, 6, 6, 50
),
(
    'PF-UNI-001',
    'Citrus Blanco',
    (SELECT id FROM categorias WHERE nombre = 'Unisex'),
    'Perfum Lab',
    'Salida citrica con te verde y musgo limpio.',
    330, 690, 25, 8, 100
),
(
    'PF-UNI-002',
    'Ambar Claro',
    (SELECT id FROM categorias WHERE nombre = 'Unisex'),
    'Perfum Lab',
    'Ambar, tonka y maderas suaves de uso diario.',
    440, 890, 12, 4, 100
),
(
    'PF-UNI-003',
    'Musk Urbano',
    (SELECT id FROM categorias WHERE nombre = 'Unisex'),
    'Perfum Lab',
    'Almizcle fresco, iris y notas limpias.',
    310, 650, 30, 10, 75
),
(
    'PF-AMB-001',
    'Bruma de Lavanda',
    (SELECT id FROM categorias WHERE nombre = 'Ambientales'),
    'Perfum Lab Home',
    'Spray ambiental con lavanda y eucalipto.',
    190, 390, 16, 5, 250
),
(
    'PF-AMB-002',
    'Vela Bosque Suave',
    (SELECT id FROM categorias WHERE nombre = 'Ambientales'),
    'Perfum Lab Home',
    'Vela aromatica con pino, cedro y vainilla.',
    160, 340, 9, 3, 200
);

INSERT INTO movimientos_inventario (
    producto_id, tipo_movimiento, cantidad,
    stock_anterior, stock_nuevo, motivo
)
SELECT id, 'ENTRADA', stock_actual, 0, stock_actual, 'Carga inicial de productos'
FROM productos
WHERE sku LIKE 'PF-%'
  AND stock_actual > 0
  AND NOT EXISTS (
      SELECT 1
      FROM movimientos_inventario
      WHERE movimientos_inventario.producto_id = productos.id
        AND movimientos_inventario.motivo = 'Carga inicial de productos'
  );
