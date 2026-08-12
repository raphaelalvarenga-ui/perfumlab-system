# Perfum Lab

Sistema de escritorio para administrar productos, inventario, clientes,
ventas, facturas y reportes de una empresa de perfumes.

## Requisitos

Antes de empezar, la computadora debe tener instalado:

- Python.
- Git.

Para verificarlo en PowerShell:

```powershell
python --version
git --version
```

Si alguno de esos comandos no funciona, primero se debe instalar Python o Git.

## Descargar el proyecto

En la computadora donde se va a instalar el sistema, abrir PowerShell y ubicarse
en la carpeta donde se quiere guardar el proyecto. Por ejemplo:

```powershell
cd C:\Users\TU_USUARIO\OneDrive\Escritorio
git clone https://github.com/raphaelalvarenga-ui/perfumlab-system.git
cd perfumlab-system
```

Importante: todos los comandos siguientes se ejecutan dentro de la carpeta
`perfumlab-system`, donde estan los archivos `README.md`, `crear_db.py`,
`requirements.txt` y `PerfumLab.spec`.

Si aparece un error como `can't open file` o `requirements.txt not found`,
casi siempre significa que PowerShell esta en la carpeta incorrecta. Se corrige
entrando a la carpeta del proyecto:

```powershell
cd C:\Users\TU_USUARIO\OneDrive\Escritorio\perfumlab-system
```

## Instalar dependencias

Desde la carpeta del proyecto:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

El archivo `requirements.txt` instala las dependencias necesarias, incluyendo:

- `openpyxl`, para importar y exportar productos en Excel.
- `pyinstaller`, para generar el ejecutable `.exe`.

## Ejecutar el programa desde el codigo

Antes de crear el `.exe`, es recomendable probar que el programa abre bien:

```powershell
python crear_db.py
python app\main.py
```

El comando `crear_db.py` crea o verifica los archivos JSON de datos en
`database/json`.

El comando `python app\main.py` abre la aplicacion en modo desarrollo.

## Generar el ejecutable .exe

Para crear el ejecutable:

```powershell
python crear_db.py
python -m PyInstaller --noconfirm --clean .\PerfumLab.spec
```

Cuando termine, el ejecutable queda en:

```text
dist\PerfumLab\PerfumLab.exe
```

Para abrirlo desde PowerShell:

```powershell
.\dist\PerfumLab\PerfumLab.exe
```

Tambien se puede abrir haciendo doble clic sobre `PerfumLab.exe`.

Importante: si se va a pasar el programa a otra computadora, se debe pasar toda
la carpeta:

```text
dist\PerfumLab
```

No se debe pasar solo el archivo `.exe`, porque la carpeta `_internal` contiene
dependencias, imagenes y archivos que el programa necesita para funcionar.

## Si PyInstaller no puede borrar dist

A veces PyInstaller falla con un error como:

```text
PermissionError: [WinError 5] Access is denied: dist\PerfumLab
```

Esto suele pasar si:

- El programa `PerfumLab.exe` esta abierto.
- Alguna ventana del Explorador de archivos esta dentro de `dist\PerfumLab`.
- OneDrive esta bloqueando o sincronizando esa carpeta.

Primero cerrar `PerfumLab.exe` y cerrar ventanas abiertas dentro de `dist`.
Luego volver a ejecutar:

```powershell
python -m PyInstaller --noconfirm --clean .\PerfumLab.spec
```

Si el error continua, generar el ejecutable en una carpeta nueva:

```powershell
python -m PyInstaller --noconfirm --clean --distpath dist_actualizado --workpath build_actualizado .\PerfumLab.spec
```

En ese caso, el ejecutable actualizado queda en:

```text
dist_actualizado\PerfumLab\PerfumLab.exe
```

Y si se va a compartir, se debe pasar toda la carpeta:

```text
dist_actualizado\PerfumLab
```

## Actualizar el proyecto desde GitHub

Si el proyecto ya estaba clonado y solo se quieren descargar cambios nuevos:

```powershell
cd C:\Users\TU_USUARIO\OneDrive\Escritorio\perfumlab-system
git switch main
git pull origin main
python -m pip install -r requirements.txt
python crear_db.py
```

Despues de actualizar el codigo, si se quiere un `.exe` actualizado, hay que
generarlo otra vez:

```powershell
python -m PyInstaller --noconfirm --clean .\PerfumLab.spec
```

El `.exe` anterior no se actualiza solo.

## Archivos importantes

- `app\main.py`: abre la aplicacion.
- `app\main_api.py`: abre la API REST con FastAPI.
- `crear_db.py`: crea o verifica los datos iniciales.
- `database\json`: contiene los datos del sistema.
- `PerfumLab.spec`: configuracion para crear el `.exe`.
- `requirements.txt`: dependencias del proyecto.
- `docs`: documentos y reportes del proyecto.

## API REST

La API REST es una capa nueva que convive con la aplicacion Tkinter. La
aplicacion de escritorio sigue usando JSON; FastAPI usa PostgreSQL, SQLAlchemy,
Alembic y autenticacion JWT.

### Instalar dependencias

Desde la carpeta principal del proyecto:

```powershell
python -m pip install -r requirements.txt
```

### Configurar variables de entorno

Crear un archivo `.env` tomando como referencia `.env.example`:

```text
APP_NAME=Perfum Lab API
APP_VERSION=1.0.0
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/perfumlab
SECRET_KEY=change_this_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
PERFUME_PROVIDER=fragella
FRAGELLA_API_KEY=
FRAGELLA_BASE_URL=https://api.fragella.com/api/v1
```

No se deben guardar contrasenas reales en el codigo. El archivo `.env` esta
ignorado por Git; `.env.example` queda versionado como plantilla.

### Crear la base PostgreSQL

Crear una base de datos llamada `perfumlab` en PostgreSQL. El usuario, clave,
host y puerto deben coincidir con `DATABASE_URL`.

Ejemplo desde `psql`:

```sql
CREATE DATABASE perfumlab;
```

### Ejecutar migraciones

Alembic toma `DATABASE_URL` desde la misma configuracion de la aplicacion:

```powershell
alembic upgrade head
```

La migracion inicial de la API crea las tablas:

- `categorias`
- `productos`

La migracion de clientes crea la tabla:

- `clientes`

La migracion de inventario crea:

- el tipo PostgreSQL `tipo_movimiento_inventario`
- `movimientos_inventario`

Las migraciones de ventas, facturas y autenticacion crean:

- `ventas`
- `detalle_ventas`
- `facturas`
- el tipo PostgreSQL `rol_usuario`
- `usuarios`
- columnas y llaves foraneas nullable de auditoria hacia `usuarios`

La migracion de informacion olfativa crea:

- el tipo PostgreSQL `tipo_nota`
- el tipo PostgreSQL `intensidad_acorde`
- `acordes`
- `notas`
- `producto_acordes`
- `producto_notas`

Para volver atras una migracion:

```powershell
alembic downgrade -1
```

### Ejecutar FastAPI

```powershell
uvicorn app.main_api:app --reload
```

Swagger queda disponible en:

```text
http://127.0.0.1:8000/docs
```

ReDoc queda disponible en:

```text
http://127.0.0.1:8000/redoc
```

### Comprobar health

```text
GET http://127.0.0.1:8000/
GET http://127.0.0.1:8000/api/v1/health
GET http://127.0.0.1:8000/api/v1/health/db
```

`/api/v1/health/db` ejecuta `SELECT 1` contra PostgreSQL. Si `DATABASE_URL` no
esta configurado o PostgreSQL no esta disponible, responde con un error
controlado sin exponer credenciales.

### Autenticacion y usuarios

La API usa access tokens JWT con `Authorization: Bearer <token>`. No hay refresh
tokens en esta fase. El token incluye `sub`, `iat`, `exp` y `ver`; cada request
protegido consulta PostgreSQL para validar que el usuario exista, este activo,
mantenga la misma `token_version` y tenga el rol actual requerido.

Antes de usar endpoints protegidos, crear el primer administrador localmente:

```powershell
uv run python scripts/create_admin.py
```

El script pide nombre, username, email opcional y contrasena con `getpass`. No
recibe contrasenas por argumentos, no imprime hashes y no crea un registro
publico.

Para iniciar sesion:

```text
POST /api/v1/auth/login
```

El login usa formulario OAuth2 compatible con Swagger:

```text
username=admin
password=...
```

Respuesta:

```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

En Swagger (`/docs`) usar el boton `Authorize` y pegar el token Bearer. Endpoints
de Auth:

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/change-password
```

`GET /api/v1/auth/me` devuelve el usuario autenticado sin `password` ni
`password_hash`. `POST /api/v1/auth/change-password` valida la contrasena actual,
hashea la nueva con Argon2 y aumenta `token_version`, por lo que los tokens
anteriores quedan invalidos.

Endpoints de usuarios, solo para `ADMINISTRADOR`:

```text
POST   /api/v1/usuarios
GET    /api/v1/usuarios
GET    /api/v1/usuarios/{id}
PATCH  /api/v1/usuarios/{id}
DELETE /api/v1/usuarios/{id}
POST   /api/v1/usuarios/{id}/reset-password
```

`DELETE` hace soft delete con `activo = false`. No borra fisicamente usuarios,
porque ventas, movimientos y facturas conservan auditoria. El reset de password
tambien incrementa `token_version`.

Roles disponibles:

```text
ADMINISTRADOR
VENDEDOR
```

Permisos principales:

```text
Publico:
GET /
GET /api/v1/health
GET /api/v1/health/db
POST /api/v1/auth/login

Cualquier usuario autenticado:
GET categorias, productos, perfil olfativo, acordes, notas, clientes,
inventario/movimientos, ventas, facturas
GET /api/v1/auth/me
POST /api/v1/auth/change-password

ADMINISTRADOR o VENDEDOR:
POST/PUT/PATCH clientes
POST ventas
POST ventas/{venta_id}/factura

Solo ADMINISTRADOR:
mutaciones de categorias, productos, perfil olfativo, acordes y notas
DELETE clientes
movimientos manuales de inventario
anular ventas
reportes
usuarios
```

Los usernames se guardan en minusculas y son unicos sin diferenciar
mayusculas/minusculas. El email es opcional; si existe, tambien se normaliza a
minusculas y es unico case-insensitive. Las contrasenas se guardan solamente
como hash Argon2.

Las nuevas ventas API guardan `ventas.usuario_id` con el usuario autenticado.
Los movimientos de inventario guardan `movimientos_inventario.usuario_id`. Las
facturas nuevas guardan `facturas.usuario_id`. Al anular una venta se guarda
`ventas.anulada_por_usuario_id`, se crean movimientos `ENTRADA` con el admin que
anulo, y si existe factura tambien queda `facturas.anulada_por_usuario_id`.

### Endpoints de categorias

```text
GET    /api/v1/categorias
GET    /api/v1/categorias/{id}
POST   /api/v1/categorias
PUT    /api/v1/categorias/{id}
PATCH  /api/v1/categorias/{id}
DELETE /api/v1/categorias/{id}
```

`DELETE` no borra fisicamente la categoria; la desactiva con `activo = false`.
No se crean productos asociados a categorias inactivas.

### Endpoints de productos

```text
GET    /api/v1/productos
GET    /api/v1/productos/{id}
POST   /api/v1/productos
PUT    /api/v1/productos/{id}
PATCH  /api/v1/productos/{id}
DELETE /api/v1/productos/{id}
```

`DELETE` no borra fisicamente el producto; lo desactiva con `activo = false`.
El precio y el costo se guardan como `Numeric/Decimal`, no como `float`.
Durante la creacion de un producto se permite definir `stock_actual` inicial.
Despues de creado, `stock_actual` no se modifica con `PUT` ni `PATCH`; cualquier
cambio de existencia debe registrarse por Inventario para mantener historial.

El listado de productos permite filtros:

```text
GET /api/v1/productos?buscar=invictus
GET /api/v1/productos?marca=Rabanne
GET /api/v1/productos?categoria_id=1
GET /api/v1/productos?genero=Hombre
GET /api/v1/productos?activo=true
GET /api/v1/productos?stock_bajo=true
GET /api/v1/productos?acorde=citrico
GET /api/v1/productos?nota=toronja
GET /api/v1/productos?nota=laurel&tipo_nota=CORAZON
```

La paginacion usa:

```text
GET /api/v1/productos?page=1&limit=20
```

`limit` acepta como maximo 100 registros por pagina.

### Informacion olfativa

La informacion olfativa vive en PostgreSQL y no cambia la aplicacion Tkinter.
La aplicacion de escritorio sigue leyendo y escribiendo JSON.

Los acordes y notas son catalogos normalizados con `nombre`, `slug`, `activo`,
`created_at` y `updated_at`. El `slug` se genera sin acentos y en minusculas:
`Citrico` y su variante con acento terminan como `citrico`. Los duplicados se
protegen con indices case-insensitive en PostgreSQL.

Endpoints de acordes:

```text
GET    /api/v1/acordes?buscar=citrico&activo=true&page=1&limit=20
GET    /api/v1/acordes/{id}
POST   /api/v1/acordes
PATCH  /api/v1/acordes/{id}
DELETE /api/v1/acordes/{id}
```

Endpoints de notas:

```text
GET    /api/v1/notas?buscar=toronja&activo=true&page=1&limit=20
GET    /api/v1/notas/{id}
POST   /api/v1/notas
PATCH  /api/v1/notas/{id}
DELETE /api/v1/notas/{id}
```

`DELETE` en acordes y notas hace soft delete con `activo = false`. Las lecturas
pueden hacerlas usuarios autenticados; las mutaciones requieren
`ADMINISTRADOR`.

El perfil olfativo de un producto se maneja separado de la respuesta normal de
productos:

```text
GET /api/v1/productos/{id}/perfil-olfativo
PUT /api/v1/productos/{id}/perfil-olfativo
```

`GET` devuelve `producto_id`, una lista de `acordes` y las `notas` agrupadas en
claves `salida`, `corazon` y `fondo`. `PUT` reemplaza el perfil completo en una
sola transaccion. No permite productos inexistentes, productos inactivos para
modificacion, acordes/notas inexistentes o inactivos, acordes repetidos ni la
misma nota repetida dentro del mismo tipo. Las posiciones deben ser cero o
positivas.

Los campos especializados de perfumeria que ya existen en `productos` se
reutilizan:

```text
genero
anio_lanzamiento
concentracion
duracion
estela
external_provider
external_id
external_last_sync
```

`duracion` representa longevity y `estela` representa sillage.

### Proveedor externo

La API queda preparada para un proveedor externo de informacion de perfumes con
una abstraccion en `app/integrations/perfume_provider.py`. Incluye DTOs
normalizados para fragancias, acordes y notas, y operaciones de busqueda,
detalle y similares.

`app/integrations/fragella_provider.py` contiene el stub `FragellaProvider`.
Mientras `FRAGELLA_API_KEY` este vacio, sus metodos lanzan
`ProviderNotConfiguredError`. No hace llamadas reales, no incluye credenciales
reales y no consume Fragella todavia.

### Endpoints de inventario

```text
POST /api/v1/inventario/entrada
POST /api/v1/inventario/salida
POST /api/v1/inventario/ajuste

GET  /api/v1/inventario/movimientos
GET  /api/v1/inventario/movimientos/{id}
```

Entrada suma unidades al `stock_actual` del producto:

```json
{
  "producto_id": 1,
  "cantidad": 10,
  "motivo": "Compra de mercaderia"
}
```

Salida resta unidades. Si la cantidad solicitada supera el stock disponible,
la API responde `400 Bad Request` y no modifica el producto:

```json
{
  "producto_id": 1,
  "cantidad": 2,
  "motivo": "Producto danado"
}
```

Ajuste recibe el stock final deseado, no una diferencia. Si el stock actual ya
es igual al valor solicitado, la operacion se rechaza para evitar movimientos
sin cambio:

```json
{
  "producto_id": 1,
  "stock_nuevo": 15,
  "motivo": "Conteo fisico"
}
```

El historial se consulta con paginacion y filtros:

```text
GET /api/v1/inventario/movimientos?producto_id=1
GET /api/v1/inventario/movimientos?tipo=ENTRADA
GET /api/v1/inventario/movimientos?desde=2026-08-12T00:00:00Z
GET /api/v1/inventario/movimientos?hasta=2026-08-12T23:59:59Z
GET /api/v1/inventario/movimientos?page=1&limit=20
```

Los movimientos son historial de auditoria: no existen endpoints para editarlos
o eliminarlos. Si hay un error de conteo, se corrige registrando un nuevo ajuste.
Las operaciones de entrada, salida y ajuste bloquean la fila del producto con
`SELECT ... FOR UPDATE` en PostgreSQL y actualizan producto + movimiento dentro
de una sola transaccion.

### Endpoints de clientes

```text
GET    /api/v1/clientes
GET    /api/v1/clientes/{id}
POST   /api/v1/clientes
PUT    /api/v1/clientes/{id}
PATCH  /api/v1/clientes/{id}
DELETE /api/v1/clientes/{id}
```

`DELETE` no borra fisicamente el cliente; lo desactiva con `activo = false`.

Ejemplo de cliente completo:

```json
{
  "nombre": "Juan Perez",
  "correo": "juan@example.com",
  "telefono": "9999-9999",
  "direccion": "La Paz"
}
```

Tambien se permite registrar clientes sin correo:

```json
{
  "nombre": "Cliente mostrador",
  "correo": null,
  "telefono": null,
  "direccion": null
}
```

Cuando el correo viene informado, se valida, se normaliza a minusculas y debe
ser unico sin diferenciar mayusculas/minusculas. Los clientes sin correo se
guardan con `correo = NULL`, por lo que pueden existir varios.

El listado de clientes permite:

```text
GET /api/v1/clientes?buscar=juan
GET /api/v1/clientes?activo=true
GET /api/v1/clientes?page=1&limit=20
```

`buscar` revisa nombre, correo y telefono. `limit` acepta como maximo 100
registros por pagina.

### Endpoints de ventas

```text
POST /api/v1/ventas

GET  /api/v1/ventas
GET  /api/v1/ventas/{id}

POST /api/v1/ventas/{id}/anular
```

Una venta se crea enviando solamente cliente opcional y productos. El servidor
toma precios desde PostgreSQL, calcula subtotales/total, descuenta stock y crea
movimientos de inventario `SALIDA`.

```json
{
  "cliente_id": 1,
  "productos": [
    {
      "producto_id": 10,
      "cantidad": 2
    },
    {
      "producto_id": 20,
      "cantidad": 1
    }
  ]
}
```

Para venta de mostrador se puede enviar `cliente_id = null` o no enviarlo. La
venta queda con:

```text
cliente_id = NULL
cliente_nombre = Cliente mostrador
```

Si el request trae productos repetidos, la API los agrupa antes de procesar la
venta. Por ejemplo, dos lineas para el producto `5` con cantidades `2` y `3`
se guardan como una linea de cantidad `5`.

Los detalles guardan snapshots historicos de:

```text
producto_sku
producto_nombre
precio_unitario
```

Si despues cambia el producto, la venta historica conserva los datos originales.
El frontend no puede enviar precio, subtotal, total, estado, stock ni usuario.

El listado de ventas permite:

```text
GET /api/v1/ventas?cliente_id=1
GET /api/v1/ventas?estado=COMPLETADA
GET /api/v1/ventas?estado=ANULADA
GET /api/v1/ventas?desde=2026-08-12T00:00:00Z
GET /api/v1/ventas?hasta=2026-08-12T23:59:59Z
GET /api/v1/ventas?page=1&limit=20
```

Para anular una venta:

```json
{
  "motivo": "Cliente cancelo la compra"
}
```

La anulacion bloquea la venta, valida que siga `COMPLETADA`, devuelve el stock
con movimientos de inventario `ENTRADA`, guarda `anulada_at` y
`motivo_anulacion`, y cambia el estado a `ANULADA`. Una venta anulada no puede
anularse de nuevo.

Crear o anular ventas es atomico: venta, detalles, cambios de stock y
movimientos de inventario se hacen en una sola transaccion PostgreSQL. Si falla
cualquier paso, se revierte todo. Para evitar carreras de stock, los productos
se bloquean con `SELECT ... FOR UPDATE` en orden de `producto_id`.

### Endpoints de facturas

```text
POST /api/v1/ventas/{venta_id}/factura

GET  /api/v1/facturas
GET  /api/v1/facturas/{id}
GET  /api/v1/facturas/numero/{numero}
```

La factura se genera desde una venta existente. El frontend no envia numero,
cliente, subtotal, total ni estado; la API toma esos valores desde la venta y
guarda snapshots historicos.

Ejemplo:

```text
POST /api/v1/ventas/15/factura
```

Una factura nueva nace como `EMITIDA`. La numeracion conserva el formato:

```text
FAC-000015
```

El numero se deriva del `venta_id`, por lo que no usa `MAX(numero)+1` y queda
protegido por indices unicos junto con la regla de una factura por venta.

Solo se facturan ventas `COMPLETADA`. Una venta `ANULADA` responde `409
Conflict`, y una venta que ya tiene factura tambien responde `409 Conflict`.

La factura conserva:

```text
cliente_nombre
subtotal
total
```

Los detalles mostrados salen de `detalle_ventas`, que ya guarda snapshots de
producto, SKU, precio unitario, cantidad y subtotal. No se recalculan precios
actuales de productos para representar facturas historicas.

El listado de facturas permite:

```text
GET /api/v1/facturas?venta_id=15
GET /api/v1/facturas?estado=EMITIDA
GET /api/v1/facturas?estado=ANULADA
GET /api/v1/facturas?buscar=FAC-000015
GET /api/v1/facturas?buscar=Juan
GET /api/v1/facturas?desde=2026-08-12T00:00:00Z
GET /api/v1/facturas?hasta=2026-08-12T23:59:59Z
GET /api/v1/facturas?page=1&limit=20
```

Si una venta facturada se anula, la misma transaccion devuelve stock, registra
movimientos de inventario `ENTRADA`, marca la venta como `ANULADA` y marca su
factura como `ANULADA`. La factura no se borra y conserva numero y detalles.
No existen endpoints para editar, borrar, reactivar o generar PDF de facturas
desde la API en esta fase.

### Endpoints de reportes

Los reportes son endpoints de solo lectura. No crean ventas, no modifican
stock, no generan facturas y no escriben datos. Todos requieren rol
`ADMINISTRADOR`.

```text
GET /api/v1/reportes/resumen
GET /api/v1/reportes/ventas
GET /api/v1/reportes/productos-mas-vendidos
GET /api/v1/reportes/stock-bajo
```

Los reportes financieros aceptan filtros de fecha ISO `YYYY-MM-DD`:

```text
GET /api/v1/reportes/resumen?desde=2026-08-01&hasta=2026-08-31
GET /api/v1/reportes/ventas?desde=2026-08-01&hasta=2026-08-31&agrupar=dia
GET /api/v1/reportes/ventas?desde=2026-01-01&hasta=2026-12-31&agrupar=mes
GET /api/v1/reportes/productos-mas-vendidos?desde=2026-08-01&hasta=2026-08-31&limit=10
```

El dia `hasta` se incluye completo usando un limite superior exclusivo: por
ejemplo, `hasta=2026-08-31` consulta registros con `created_at < 2026-09-01
00:00:00`.

Las ventas `ANULADA` no cuentan como ingresos, unidades vendidas, productos mas
vendidos ni ventas exitosas. Solo aparecen en metricas separadas, como
`ventas_anuladas`. Las facturas validas cuentan solamente si estan `EMITIDA`;
las facturas `ANULADA` se reportan por separado.

`GET /api/v1/reportes/resumen` devuelve metricas para dashboard:

```json
{
  "periodo": {
    "desde": "2026-08-01",
    "hasta": "2026-08-31"
  },
  "ventas_completadas": 25,
  "ventas_anuladas": 2,
  "ingresos_totales": "12450.00",
  "ticket_promedio": "498.00",
  "unidades_vendidas": 56,
  "facturas_emitidas": 20,
  "facturas_anuladas": 1,
  "productos_stock_bajo": 4
}
```

`GET /api/v1/reportes/ventas` genera la tendencia para una futura grafica. El
parametro `agrupar` acepta `dia` o `mes`, y los periodos salen en orden
cronologico ascendente.

`GET /api/v1/reportes/productos-mas-vendidos` usa `detalle_ventas.cantidad` y
`detalle_ventas.subtotal`, por lo que respeta precios, SKU y nombres historicos
guardados al momento de vender. No recalcula ingresos con el precio actual del
producto. `limit` acepta valores de 1 a 100.

`GET /api/v1/reportes/stock-bajo?page=1&limit=20` lista productos activos con
`stock_actual <= stock_minimo`. Este reporte representa el inventario actual y
no depende del rango historico de fechas. El campo `faltante_minimo` se calcula
como `max(stock_minimo - stock_actual, 0)` y se ordenan primero los productos
con mayor deficit.

## Notas sobre carpetas generadas

Las carpetas `dist`, `dist_actualizado`, `build` y `build_actualizado` son
generadas por PyInstaller y normalmente no se suben al repositorio.

Cada computadora puede generar su propio ejecutable siguiendo los pasos de este
README.
