# perfumlab-system
Sistema funcional para una empresa de perfumes.

## Actualizar el proyecto desde GitHub

Para que otro integrante del equipo reciba los cambios subidos a la rama
`main`, debe ejecutar estos comandos dentro de la carpeta del proyecto:

```bash
git switch main
git pull origin main
```

Si la computadora todavia no tiene la rama `main` creada localmente:

```bash
git fetch origin
git switch -c main origin/main
```

Antes de hacer `pull`, es recomendable revisar si hay cambios locales sin
guardar:

```bash
git status
```

## Sobre la carpeta dist

La carpeta `dist/` no aparece al hacer `git pull` porque esta ignorada en
`.gitignore`. Esa carpeta es generada por PyInstaller y normalmente no se sube
al repositorio.

Cada computadora debe generar su propio `dist/` despues de descargar el codigo.

## Ejecutar el programa

Desde la raiz del proyecto:

```powershell
cd C:\Users\yesid\OneDrive\Escritorio\perfumelabsystem\perfumlab-system
uv run python crear_db.py
uv run python app\main.py
```

El comando `crear_db.py` crea o verifica los archivos JSON en `database/json/`.
El comando `app\main.py` abre la ventana principal del sistema.

Si Python esta instalado directamente en la computadora, tambien se puede usar:

```powershell
python crear_db.py
python app\main.py
```

## Generar el ejecutable

Desde la raiz del proyecto:

```bash
python crear_db.py
pyinstaller PerfumLab.spec
```

El comando `python crear_db.py` inicializa los archivos JSON de datos en
`database/json/`. Al finalizar, PyInstaller crea la carpeta:

```text
dist/PerfumLab/
```

Dentro de esa carpeta queda el ejecutable del sistema.

Si PyInstaller no esta instalado:

```bash
pip install pyinstaller
```

## Generar el exe en otra computadora

En una computadora nueva, primero se descarga el proyecto desde GitHub:

```bash
git clone https://github.com/raphaelalvarenga-ui/perfumlab-system.git
cd perfumlab-system
git switch main
```

Luego se instala PyInstaller, se crean los archivos JSON y se genera el
ejecutable:

```bash
python -m pip install pyinstaller
python crear_db.py
python -m PyInstaller PerfumLab.spec
```

Cuando termine, el ejecutable queda en:

```text
dist\PerfumLab\PerfumLab.exe
```

Para abrirlo desde PowerShell:

```powershell
.\dist\PerfumLab\PerfumLab.exe
```

Importante: si se va a pasar el programa a otra computadora, se debe pasar
toda la carpeta `dist\PerfumLab`, no solo el archivo `.exe`, porque esa carpeta
incluye dependencias, imagenes y archivos necesarios para que funcione.

## Subir el archivo PerfumLab.spec

El archivo `PerfumLab.spec` contiene la configuracion para generar el
ejecutable. Si no aparece en GitHub porque esta ignorado por `.gitignore`, se
puede subir forzadamente con:

```bash
git add -f PerfumLab.spec
git commit -m "agregar configuracion para generar exe"
git push origin main
```

## Subir dist manualmente

No es lo recomendado, pero si por alguna razon se necesita subir el ejecutable
generado a GitHub, se puede hacer forzando la carpeta `dist/`:

```bash
git add -f dist/
git commit -m "agregar ejecutable compilado"
git push origin main
```

Lo mas limpio para trabajar en equipo es subir el codigo y el archivo
`PerfumLab.spec`, y que cada integrante genere su propio `dist/` localmente.
