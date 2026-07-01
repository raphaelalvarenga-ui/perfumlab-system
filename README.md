# perfumlab-system
Sistema funcional para una empresa de perfumes.

## Actualizar el proyecto desde GitHub

Para que otro integrante del equipo reciba los cambios subidos a la rama
`develop`, debe ejecutar estos comandos dentro de la carpeta del proyecto:

```bash
git switch develop
git pull origin develop
```

Si la computadora todavia no tiene la rama `develop` creada localmente:

```bash
git fetch origin
git switch -c develop origin/develop
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

## Generar el ejecutable

Desde la raiz del proyecto:

```bash
python crear_db.py
pyinstaller PerfumLab.spec
```

Al finalizar, PyInstaller crea la carpeta:

```text
dist/PerfumLab/
```

Dentro de esa carpeta queda el ejecutable del sistema.

Si PyInstaller no esta instalado:

```bash
pip install pyinstaller
```

## Subir el archivo PerfumLab.spec

El archivo `PerfumLab.spec` contiene la configuracion para generar el
ejecutable. Si no aparece en GitHub porque esta ignorado por `.gitignore`, se
puede subir forzadamente con:

```bash
git add -f PerfumLab.spec
git commit -m "agregar configuracion para generar exe"
git push origin develop
```

## Subir dist manualmente

No es lo recomendado, pero si por alguna razon se necesita subir el ejecutable
generado a GitHub, se puede hacer forzando la carpeta `dist/`:

```bash
git add -f dist/
git commit -m "agregar ejecutable compilado"
git push origin develop
```

Lo mas limpio para trabajar en equipo es subir el codigo y el archivo
`PerfumLab.spec`, y que cada integrante genere su propio `dist/` localmente.
