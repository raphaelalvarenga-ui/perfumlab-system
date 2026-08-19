# Perfum Lab

Perfum Lab es un sistema empresarial de gestion de perfumeria. Permite
administrar productos, categorias, inventario, clientes, ventas, facturas,
reportes y perfiles olfativos de fragancias desde una aplicacion de escritorio
Tkinter conectada a una API REST FastAPI.

Estado verificado de esta copia del repositorio: `2026-08-19`.

## Resumen

| Area | Estado actual |
| --- | --- |
| Aplicacion de escritorio | `PerfumLab.exe` / Tkinter |
| Backend | FastAPI REST API |
| Base de datos activa | PostgreSQL, en produccion alojada en Neon |
| Despliegue backend | Vercel |
| API publica actual | `https://perfumlab-system.vercel.app` |
| Proveedor externo | Fragella API, consumida solo desde FastAPI |
| Persistencia legacy | JSON conservado para compatibilidad, pruebas y migracion, no como almacenamiento principal |
| Migracion Alembic head | `20260812_0008` |
| Suite de pruebas documentada | `uv run pytest` |

## Arquitectura

La arquitectura de produccion es:

```text
PerfumLab.exe / Tkinter
        |
        | HTTPS + REST + JWT
        v
FastAPI REST API
        |
        | SQLAlchemy + psycopg
        v
PostgreSQL / Neon

FastAPI REST API
        |
        | httpx + x-api-key
        v
Fragella API
```

La aplicacion de escritorio no se conecta directamente a PostgreSQL ni a
Fragella. El EXE solo conoce la URL publica de la API y guarda el JWT de sesion
en memoria. Fragella se consume exclusivamente desde el backend, lo que evita
exponer la API key en el cliente de escritorio y permite controlar cuota,
timeouts, reintentos y errores externos en un solo lugar.

Los archivos JSON historicos siguen en `database/json`, y algunas capas aceptan
`ruta_db` para pruebas o compatibilidad legacy. En el flujo productivo actual,
Tkinter usa la API REST y PostgreSQL es la fuente activa de datos.

## Tecnologias

Las dependencias versionadas estan en `requirements.txt`. Esta copia del repo no
contiene `pyproject.toml` ni `uv.lock`; por eso la instalacion base usa
`requirements.txt`. `uv` se usa como runner de comandos cuando esta disponible.

Tecnologias y librerias principales:

- Python
- Tkinter
- FastAPI
- PostgreSQL / Neon
- SQLAlchemy
- Alembic
- Pydantic / pydantic-settings
- httpx
- JWT con PyJWT
- Hash de passwords con `pwdlib[argon2]`
- pytest
- PyInstaller
- openpyxl
- Vercel
- Fragella API
- Dockerfile opcional para backend

## Estructura del proyecto

```text
app/
  api/                  Rutas FastAPI, dependencias y router /api/v1
  api_client/           Cliente REST usado por Tkinter
  controllers/          Controladores de escritorio con modo API y compatibilidad JSON
  core/                 Configuracion, seguridad y utilidades comunes
  database/             Sesion SQLAlchemy y almacenamiento JSON legacy
  facturas/             Pantalla y exportacion PDF/TXT desde escritorio
  integrations/         Abstraccion de proveedor y FragellaProvider
  models/               Modelos de dominio y ORM
  repositories/         Acceso a datos SQLAlchemy
  reportes/             Reportes de escritorio, CSV y Excel de productos
  schemas/              Esquemas Pydantic
  services/             Logica de negocio y transacciones
  ventas/               Pantalla de ventas de escritorio
  views/                Vistas Tkinter de productos y clientes
  desktop_config.py     Configuracion segura del desktop
  index.py              Entrada compatible con Vercel
  main.py               Entrada de la aplicacion Tkinter
  main_api.py           Entrada de FastAPI
alembic/
  versions/             Migraciones PostgreSQL
assets/
  logo/                 Iconos y logos usados por el EXE
database/json/          Datos historicos legacy
deploy/                 Guia corta de despliegue
docs/                   Documentacion del proyecto
scripts/                Admin, backup, migracion JSON, build y smoke del EXE
tests/                  Pruebas API, cliente REST, integraciones, migracion y QA
PerfumLab.spec          Configuracion PyInstaller onedir
Dockerfile              Imagen opcional para FastAPI
requirements.txt        Dependencias del proyecto
alembic.ini             Configuracion Alembic
```

## Modulos funcionales

### Autenticacion y usuarios

- Login por `POST /api/v1/auth/login`.
- Sesion con JWT `Authorization: Bearer <token>`.
- Consulta de usuario autenticado con `GET /api/v1/auth/me`.
- Cambio de password con invalidacion de tokens anteriores.
- Roles reales:
  - `ADMINISTRADOR`
  - `VENDEDOR`
- Usuarios administrados por endpoints bajo `/api/v1/usuarios`.
- Passwords almacenados solo como hash.
- Auditoria de usuario en ventas, movimientos de inventario, facturas y
  anulaciones.

### Categorias

- CRUD de categorias por API.
- Soft delete con `activo = false`.
- Nombre unico case-insensitive.
- Productos no pueden asociarse a categorias inactivas.

### Productos

- CRUD de productos por API.
- SKU unico case-insensitive.
- Campos principales: SKU, nombre, categoria, marca, descripcion, costo,
  precio, stock actual, stock minimo y estado activo/inactivo.
- Campos especializados de perfumeria: genero, anio de lanzamiento,
  concentracion, duracion, estela y metadatos externos.
- Busqueda y filtros por texto, marca, categoria, genero, activo, stock bajo,
  acorde, nota y tipo de nota.
- El stock inicial puede indicarse al crear producto. Despues, los cambios de
  stock se hacen por Inventario para conservar historial.

### Inventario

- Movimientos reales:
  - `ENTRADA`
  - `SALIDA`
  - `AJUSTE`
- Registro de cantidad, stock anterior, stock nuevo, motivo, fecha y usuario.
- Operaciones atomicas con bloqueo de fila del producto.
- Historial consultable por producto, tipo y rango de fechas.
- No existen endpoints para editar o borrar movimientos; un error se corrige
  con un nuevo ajuste.

### Clientes

- CRUD de clientes por API.
- Clientes con o sin correo.
- Correos normalizados a minusculas y unicos case-insensitive cuando existen.
- Soft delete con `activo = false`.
- Busqueda por nombre, correo y telefono.

### Ventas

- Registro de ventas con cliente opcional.
- Venta de mostrador cuando `cliente_id` es nulo.
- Productos repetidos en el request se agrupan antes de procesar.
- El backend toma precios desde PostgreSQL, calcula subtotales y total.
- Descuento de inventario mediante movimientos `SALIDA`.
- Estados reales: `COMPLETADA` y `ANULADA`.
- Anulacion con reposicion de stock, movimientos `ENTRADA`, motivo y auditoria.
- Snapshots historicos de SKU, nombre y precio en `detalle_ventas`.

### Facturas

- Facturacion asociada a ventas con `POST /api/v1/ventas/{venta_id}/factura`.
- Numeracion derivada del ID de venta con formato `FAC-000015`.
- Estados reales: `EMITIDA` y `ANULADA`.
- Una venta solo puede tener una factura.
- Si una venta facturada se anula, la factura queda `ANULADA`.
- La API consulta factura y detalle, pero no expone endpoint PDF.
- La aplicacion Tkinter genera y exporta PDF desde `app/facturas/facturas.py`
  usando los datos consultados por la API.

### Reportes

Reportes FastAPI de solo lectura, restringidos a `ADMINISTRADOR`:

- Resumen operativo.
- Ventas agrupadas por dia o mes.
- Productos mas vendidos.
- Bajo stock.

La aplicacion de escritorio muestra reportes y permite exportar CSV. La vista de
productos permite exportar e importar inventario en Excel con `openpyxl`.

## Perfil olfativo

El backend tiene un modelo normalizado para informacion olfativa:

- `acordes`
- `notas`
- Tipos de nota:
  - `SALIDA`
  - `CORAZON`
  - `FONDO`
- Relacion `producto_acordes`.
- Relacion `producto_notas`.
- Intensidades de acordes:
  - `DOMINANTE`
  - `PROMINENTE`
  - `MODERADO`
  - `SUTIL`

Endpoints reales:

```text
GET /api/v1/acordes
GET /api/v1/acordes/{acorde_id}
POST /api/v1/acordes
PATCH /api/v1/acordes/{acorde_id}
DELETE /api/v1/acordes/{acorde_id}

GET /api/v1/notas
GET /api/v1/notas/{nota_id}
POST /api/v1/notas
PATCH /api/v1/notas/{nota_id}
DELETE /api/v1/notas/{nota_id}

GET /api/v1/productos/{producto_id}/perfil-olfativo
PUT /api/v1/productos/{producto_id}/perfil-olfativo
```

`GET /perfil-olfativo` devuelve los acordes y las notas agrupadas por salida,
corazon y fondo. `PUT /perfil-olfativo` reemplaza el perfil completo en una sola
transaccion y requiere rol `ADMINISTRADOR`.

## Perfil olfativo en el EXE

La aplicacion Tkinter ya visualiza el perfil olfativo desde la pantalla
`Productos e inventario`.

Flujo implementado:

```text
ProductosView
    |
    v
ProductosController
    |
    v
ProductosApi
    |
    v
GET /api/v1/productos/{producto_id}/perfil-olfativo
    |
    v
PostgreSQL / Neon
```

Archivos involucrados:

- `app/api_client/productos.py`
- `app/controllers/productos_controller.py`
- `app/views/productos_view.py`

Al seleccionar un producto, el panel derecho puede mostrar:

- Acordes principales.
- Notas de salida.
- Notas de corazon.
- Notas de fondo.

Esta visualizacion lee datos ya almacenados en PostgreSQL. No hace una llamada a
Fragella cada vez que se abre o selecciona un producto. Esto es importante para
controlar la cuota del proveedor externo y para mantener una experiencia rapida
en el EXE.

## Integracion Fragella

Proveedor externo: Fragella.

La integracion se configura con variables de entorno del backend:

```text
PERFUME_PROVIDER=fragella
FRAGELLA_API_KEY=YOUR_FRAGELLA_API_KEY
FRAGELLA_BASE_URL=https://api.fragella.com/api/v1
FRAGELLA_TIMEOUT_SECONDS=10
```

No se debe incluir la API key en el cliente de escritorio, logs, respuestas JSON,
Swagger, Git ni bases de datos. El backend usa `httpx` y envia la key con el
header `x-api-key`.

Rutas reales:

```text
GET  /api/v1/integraciones/fragella/status
GET  /api/v1/integraciones/fragella/usage

GET  /api/v1/productos/{producto_id}/proveedor/candidatos?limit=5
GET  /api/v1/productos/{producto_id}/proveedor/candidatos/{external_id}
POST /api/v1/productos/{producto_id}/sincronizar-proveedor
GET  /api/v1/productos/{producto_id}/similares?limit=5
```

Capacidades implementadas:

- Comprobar si Fragella esta configurado.
- Consultar uso/cuota.
- Buscar candidatos para asociar un producto local con una fragancia externa.
- Obtener preview/detalle de un candidato.
- Sincronizar datos del proveedor hacia PostgreSQL.
- Consultar perfumes similares.

La sincronizacion guarda localmente:

- `external_provider`
- `external_id`
- `external_last_sync`
- `external_image_url`
- `external_transparent_image_url`
- Metadatos disponibles: genero, anio, concentracion, duracion y estela.
- Acordes.
- Notas de salida, corazon y fondo.

La sincronizacion no modifica datos de negocio como SKU, nombre, marca, costo,
precio, stock, categoria o estado activo. Si Fragella devuelve `None` para un
metadato, se conserva el valor local existente.

### Notas sobre cuota y disponibilidad

Las operaciones que consultan Fragella dependen de disponibilidad, plan y cuota
del proveedor. Los perfiles ya sincronizados se leen desde PostgreSQL y no
consumen nuevas solicitudes a Fragella. La consulta de similares existe en el
backend, pero durante pruebas reales puede quedar limitada por cuota/rate limit
del proveedor; eso no bloquea la funcionalidad principal de productos, perfil
olfativo sincronizado y visualizacion en escritorio.

## Endpoints principales

Todos los endpoints bajo `/api/v1`, excepto health y login, requieren JWT.

### Salud

```text
GET /
GET /api/v1/health
GET /api/v1/health/db
```

`/api/v1/health/db` ejecuta una comprobacion simple contra PostgreSQL sin
exponer credenciales.

### Auth y usuarios

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/change-password

POST   /api/v1/usuarios
GET    /api/v1/usuarios
GET    /api/v1/usuarios/{usuario_id}
PATCH  /api/v1/usuarios/{usuario_id}
DELETE /api/v1/usuarios/{usuario_id}
POST   /api/v1/usuarios/{usuario_id}/reset-password
```

### Categorias

```text
GET    /api/v1/categorias
GET    /api/v1/categorias/{categoria_id}
POST   /api/v1/categorias
PUT    /api/v1/categorias/{categoria_id}
PATCH  /api/v1/categorias/{categoria_id}
DELETE /api/v1/categorias/{categoria_id}
```

### Productos

```text
GET    /api/v1/productos
GET    /api/v1/productos/{producto_id}
POST   /api/v1/productos
PUT    /api/v1/productos/{producto_id}
PATCH  /api/v1/productos/{producto_id}
DELETE /api/v1/productos/{producto_id}
```

Filtros confirmados:

```text
buscar
marca
categoria_id
genero
activo
stock_bajo
acorde
nota
tipo_nota
page
limit
```

### Inventario

```text
POST /api/v1/inventario/entrada
POST /api/v1/inventario/salida
POST /api/v1/inventario/ajuste

GET  /api/v1/inventario/movimientos
GET  /api/v1/inventario/movimientos/{movimiento_id}
```

### Clientes

```text
GET    /api/v1/clientes
GET    /api/v1/clientes/{cliente_id}
POST   /api/v1/clientes
PUT    /api/v1/clientes/{cliente_id}
PATCH  /api/v1/clientes/{cliente_id}
DELETE /api/v1/clientes/{cliente_id}
```

### Ventas

```text
POST /api/v1/ventas
GET  /api/v1/ventas
GET  /api/v1/ventas/{venta_id}
POST /api/v1/ventas/{venta_id}/anular
```

### Facturas

```text
POST /api/v1/ventas/{venta_id}/factura
GET  /api/v1/facturas
GET  /api/v1/facturas/{factura_id}
GET  /api/v1/facturas/numero/{numero}
```

### Reportes

```text
GET /api/v1/reportes/resumen
GET /api/v1/reportes/ventas
GET /api/v1/reportes/productos-mas-vendidos
GET /api/v1/reportes/stock-bajo
```

## Permisos por rol

| Accion | ADMINISTRADOR | VENDEDOR |
| --- | --- | --- |
| Login y `/auth/me` | Si | Si |
| Lectura de categorias/productos/clientes/ventas/facturas/inventario | Si | Si |
| Crear/editar clientes | Si | Si |
| Crear ventas | Si | Si |
| Emitir facturas | Si | Si |
| Reportes | Si | No |
| Usuarios | Si | No |
| Mutar categorias/productos/acordes/notas/perfil olfativo | Si | No |
| Movimientos manuales de inventario | Si | No |
| Anular ventas | Si | No |
| Fragella status, usage, candidatos, preview y sync | Si | No |
| Consultar similares | Si | Si |

## Configuracion de backend

El backend lee configuracion desde variables de entorno y `.env` mediante
`app/core/config.py`.

Variables confirmadas:

```text
APP_NAME
APP_VERSION
APP_ENV
DATABASE_URL
SECRET_KEY
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
CORS_ORIGINS
CORS_ALLOW_CREDENTIALS
ENABLE_DOCS
LOG_LEVEL
PERFUME_PROVIDER
FRAGELLA_API_KEY
FRAGELLA_BASE_URL
FRAGELLA_TIMEOUT_SECONDS
```

Ejemplo seguro para desarrollo:

```env
APP_NAME=Perfum Lab API
APP_VERSION=1.0.0
APP_ENV=development
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DATABASE
SECRET_KEY=CHANGE_ME_IN_LOCAL_DEVELOPMENT
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
CORS_ALLOW_CREDENTIALS=true
ENABLE_DOCS=true
LOG_LEVEL=INFO

PERFUME_PROVIDER=fragella
FRAGELLA_API_KEY=YOUR_FRAGELLA_API_KEY
FRAGELLA_BASE_URL=https://api.fragella.com/api/v1
FRAGELLA_TIMEOUT_SECONDS=10
```

Reglas de produccion confirmadas:

- `APP_ENV=production` exige `DATABASE_URL`.
- `DATABASE_URL` debe usar PostgreSQL.
- `SECRET_KEY` debe ser fuerte, no placeholder y tener longitud suficiente.
- Si `CORS_ALLOW_CREDENTIALS=true`, `CORS_ORIGINS` no puede incluir `*`.
- `ENABLE_DOCS=false` deshabilita `/docs`, `/redoc` y `/openapi.json`.
- Los secretos deben gestionarse como variables de entorno del proveedor de
  despliegue, nunca hardcodeados ni versionados.

## Configuracion del escritorio

La aplicacion de escritorio usa `app/desktop_config.py` y admite configuracion
por archivo `perfumlab_desktop.json` o variables de entorno:

```text
PERFUMLAB_DESKTOP_MODE
PERFUMLAB_API_URL
PERFUMLAB_API_TIMEOUT_SECONDS
```

Ejemplo para desarrollo:

```env
PERFUMLAB_DESKTOP_MODE=development
PERFUMLAB_API_URL=http://127.0.0.1:8000
PERFUMLAB_API_TIMEOUT_SECONDS=10
```

Ejemplo seguro para produccion, colocado junto a `PerfumLab.exe`:

```json
{
  "api_url": "https://perfumlab-system.vercel.app",
  "timeout_seconds": 15,
  "mode": "production",
  "app_name": "Perfum Lab",
  "version": "1.0.0"
}
```

En `production`, `validate_desktop_api_url()` exige `https://` y rechaza
localhost (`localhost`, `127.0.0.1`, `::1`). El EXE no debe recibir
`DATABASE_URL`, `SECRET_KEY`, passwords de PostgreSQL ni `FRAGELLA_API_KEY`.

## Instalacion local

Requisitos:

- Python
- Git
- PostgreSQL accesible por `DATABASE_URL`
- `uv` opcional, recomendado para ejecutar los comandos documentados

Clonar el repositorio:

```powershell
cd C:\Users\TU_USUARIO\OneDrive\Escritorio
git clone https://github.com/raphaelalvarenga-ui/perfumlab-system.git
cd perfumlab-system
```

Crear entorno e instalar dependencias desde `requirements.txt`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Configurar `.env` usando `.env.example` como plantilla, sin copiar secretos
reales al repositorio.

Crear o apuntar a una base PostgreSQL y aplicar migraciones:

```powershell
uv run alembic upgrade head
```

Crear el primer administrador:

```powershell
uv run python scripts/create_admin.py
```

Levantar FastAPI en desarrollo:

```powershell
uv run uvicorn app.main_api:app --reload
```

Ejecutar Tkinter en otra terminal:

```powershell
uv run python -m app.main
```

Al iniciar, Tkinter comprueba:

```text
GET /api/v1/health
GET /api/v1/health/db
```

Si la API o PostgreSQL no estan disponibles, muestra un mensaje claro y no abre
los modulos empresariales.

## Produccion en Vercel y Neon

El backend esta desplegado en Vercel:

```text
https://perfumlab-system.vercel.app
```

La entrada compatible con Vercel es:

```python
from app.main_api import app
```

en `app/index.py`.

Endpoints publicos verificados el `2026-08-19`:

```text
GET https://perfumlab-system.vercel.app/
GET https://perfumlab-system.vercel.app/api/v1/health
GET https://perfumlab-system.vercel.app/api/v1/health/db
```

Resultados observados:

- API: `{"status":"running"}` en `/`.
- Health: `{"status":"ok"}`.
- PostgreSQL: `{"status":"ok","database":"connected"}`.
- `/docs` y `/openapi.json`: `404`, coherente con docs deshabilitadas por
  `ENABLE_DOCS=false` en produccion.

La base de datos de produccion esta alojada en Neon PostgreSQL. Solo debe
documentarse que `DATABASE_URL` apunta a PostgreSQL; no se deben publicar
hostnames privados, usuarios, passwords ni connection strings reales.

## Migraciones

Alembic toma `DATABASE_URL` desde la configuracion de la aplicacion. El head
actual del repositorio es `20260812_0008`.

| Revision | Contenido principal |
| --- | --- |
| `20260810_0001` | Categorias y productos, incluyendo campos base de perfumeria |
| `20260811_0002` | Clientes |
| `20260812_0003` | Movimientos de inventario y enum `tipo_movimiento_inventario` |
| `20260812_0004` | Ventas, detalle de ventas y enum `estado_venta` |
| `20260812_0005` | Facturas y enum `estado_factura` |
| `20260812_0006` | Usuarios, roles, auth y auditoria en ventas, inventario y facturas |
| `20260812_0007` | Acordes, notas, relaciones con productos y enums olfativos |
| `20260812_0008` | URLs externas de imagen y unicidad `external_provider + external_id` |

Aplicar migraciones:

```powershell
uv run alembic upgrade head
```

Revertir una migracion en entorno controlado:

```powershell
uv run alembic downgrade -1
```

Las migraciones no se ejecutan desde requests HTTP ni desde el EXE.

## Migracion desde JSON legacy

La migracion JSON a PostgreSQL es una herramienta puntual para trasladar datos
historicos. Despues de migrar, la aplicacion de escritorio debe operar contra
REST API y PostgreSQL.

Auditar sin escribir:

```powershell
uv run python scripts/audit_legacy_data.py
```

Simular migracion:

```powershell
uv run python scripts/migrate_json_to_postgres.py --dry-run
```

Aplicar migracion real:

```powershell
uv run python scripts/migrate_json_to_postgres.py --apply
```

La migracion real crea backups de JSON y PostgreSQL, valida conflictos, preserva
IDs legacy cuando es seguro y aplica los cambios en una sola transaccion. Los
usuarios legacy se auditan, pero no se migran passwords.

## Build del EXE

El proyecto usa PyInstaller con `PerfumLab.spec`. La configuracion es `onedir`,
por lo que el resultado esperado es una carpeta completa:

```text
dist/PerfumLab/PerfumLab.exe
```

Comando validado con el `.spec`:

```powershell
uv run pyinstaller PerfumLab.spec --clean --noconfirm
```

Comando recomendado para generar tambien `perfumlab_desktop.json`:

```powershell
uv run python scripts/build_desktop.py --mode production --api-url https://perfumlab-system.vercel.app
```

Salida esperada del script:

```text
dist/PerfumLab/PerfumLab.exe
dist/PerfumLab/perfumlab_desktop.json
```

Para entregar el escritorio, se debe copiar la carpeta completa
`dist/PerfumLab`, no solo el `.exe`, porque PyInstaller en modo `onedir` genera
archivos internos y recursos que el ejecutable necesita.

`PerfumLab.spec` incluye assets de logo, pero no empaqueta `.env`, scripts
administrativos, Alembic ni `database/json/*.json` como datos de produccion.

Smoke opcional del EXE:

```powershell
uv run python scripts/smoke_desktop_exe.py --api-url https://perfumlab-system.vercel.app
```

## Tests

La suite de pruebas cubre API, cliente REST, integraciones, migracion legacy,
configuracion de produccion y flujos QA de escritorio/legacy.

Comando:

```powershell
uv run pytest
```

Cobertura funcional incluida:

- Health y root.
- Auth, JWT, permisos, usuarios y auditoria.
- Categorias.
- Productos.
- Inventario.
- Clientes.
- Ventas.
- Facturas.
- Reportes.
- Acordes.
- Notas.
- Perfil olfativo.
- Integracion de proveedor de perfumes.
- FragellaProvider.
- API client usado por Tkinter.
- Configuracion desktop.
- Migracion JSON a PostgreSQL.
- Validaciones de produccion.
- QA core, exportacion CSV/PDF y Excel.

El ultimo resultado documentado para la suite completa fue:

```text
185 passed, 1 warning
```

El warning corresponde a una deprecacion de `TestClient`/`httpx` en el entorno
de pruebas y no se considera un error funcional.

## Validacion end-to-end realizada

Se realizaron pruebas funcionales y end-to-end sobre el sistema desplegado y el
EXE. No significa que todos los casos posibles del universo esten cubiertos,
pero si valida los flujos principales:

- Login de administrador desde el EXE.
- Categorias.
- Creacion y consulta de productos.
- Inventario: entrada, salida y movimientos.
- Clientes.
- Venta.
- Descuento de stock.
- Facturacion.
- Generacion de PDF desde escritorio.
- Reportes.
- API health.
- Conexion a PostgreSQL.
- Fragella status.
- Fragella usage.
- Busqueda de candidatos.
- Sincronizacion real de una fragancia.
- Persistencia de acordes y notas.
- Consulta del perfil olfativo desde PostgreSQL.
- Visualizacion de acordes y notas en la aplicacion de escritorio.

La sincronizacion real se valido con el producto de prueba `Invictus Legend` de
`Paco Rabanne` y el external ID
`invictus-legend-paco-rabanne-for-men`. La respuesta de sincronizacion indico
metadatos actualizados, 10 acordes y 8 notas. Ese perfume fue un dato de prueba
para validar la integracion, no informacion hardcodeada del sistema.

## Backup y operacion

Backup PostgreSQL:

```powershell
uv run python scripts/backup_postgres.py
```

El script lee `DATABASE_URL`, usa `pg_dump`, no imprime passwords y genera
backups bajo `backups/`.

Restore manual en entorno controlado:

```powershell
pg_restore --clean --if-exists --dbname "<DATABASE_URL_DESTINO>" backups\archivo.dump
```

Para backup SQL plano:

```powershell
uv run python scripts/backup_postgres.py --format plain
psql "<DATABASE_URL_DESTINO>" -f backups\archivo.sql
```

No hay restore automatico desde la aplicacion.

## Estado actual y pendientes conocidos

- Produccion usa Vercel + Neon y health/db responde correctamente.
- La documentacion interactiva puede estar deshabilitada en produccion con
  `ENABLE_DOCS=false`.
- El EXE consume la API REST y no debe conectarse directo a Fragella.
- El perfil olfativo en el EXE es lectura desde PostgreSQL.
- Las llamadas a Fragella dependen de la cuota y disponibilidad del proveedor.
- La consulta de similares existe en backend, pero puede verse limitada por
  rate limit o cuota del plan externo.
- No hay auto-update ni instalador final documentado; el entregable actual es
  la carpeta `dist/PerfumLab` generada por PyInstaller.
- JSON queda como legado, pruebas y migracion, no como fuente activa de
  produccion.

## Comandos rapidos

```powershell
# Instalar dependencias
python -m pip install -r requirements.txt

# Migrar base
uv run alembic upgrade head

# Crear admin
uv run python scripts/create_admin.py

# API local
uv run uvicorn app.main_api:app --reload

# Desktop local
uv run python -m app.main

# Tests
uv run pytest

# EXE
uv run python scripts/build_desktop.py --mode production --api-url https://perfumlab-system.vercel.app
```
