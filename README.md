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

La API REST es una capa nueva que convive con la aplicacion Tkinter. En esta
fase solo incluye endpoints de diagnostico y deja preparada la conexion con
PostgreSQL, SQLAlchemy y Alembic.

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
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
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

El listado de productos permite filtros:

```text
GET /api/v1/productos?buscar=invictus
GET /api/v1/productos?marca=Rabanne
GET /api/v1/productos?categoria_id=1
GET /api/v1/productos?genero=Hombre
GET /api/v1/productos?activo=true
GET /api/v1/productos?stock_bajo=true
```

La paginacion usa:

```text
GET /api/v1/productos?page=1&limit=20
```

`limit` acepta como maximo 100 registros por pagina.

## Notas sobre carpetas generadas

Las carpetas `dist`, `dist_actualizado`, `build` y `build_actualizado` son
generadas por PyInstaller y normalmente no se suben al repositorio.

Cada computadora puede generar su propio ejecutable siguiendo los pasos de este
README.
