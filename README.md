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
- `crear_db.py`: crea o verifica los datos iniciales.
- `database\json`: contiene los datos del sistema.
- `PerfumLab.spec`: configuracion para crear el `.exe`.
- `requirements.txt`: dependencias del proyecto.
- `docs`: documentos y reportes del proyecto.

## Notas sobre carpetas generadas

Las carpetas `dist`, `dist_actualizado`, `build` y `build_actualizado` son
generadas por PyInstaller y normalmente no se suben al repositorio.

Cada computadora puede generar su propio ejecutable siguiendo los pasos de este
README.
