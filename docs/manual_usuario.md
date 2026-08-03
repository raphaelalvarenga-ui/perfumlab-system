# Manual de usuario - Perfum Lab

## 1. Objetivo del sistema

Perfum Lab es un sistema de escritorio para administrar productos, inventario,
ventas, facturas y reportes de una empresa de perfumes.

El sistema guarda la informacion en archivos JSON dentro de la carpeta:

```text
database/json/
```

## 2. Como abrir el sistema

Desde la carpeta principal del proyecto, ejecutar:

```powershell
python crear_db.py
python app\main.py
```

Tambien se puede usar:

```powershell
uv run python crear_db.py
uv run python app\main.py
```

El archivo `crear_db.py` crea o verifica los archivos de datos. El archivo
`app\main.py` abre la ventana principal del sistema.

## 3. Pantalla principal

Al abrir Perfum Lab aparece el menu principal con estos modulos:

- Productos e inventario
- Ventas
- Facturas
- Reportes

Para entrar a un modulo, presionar el boton **Abrir**. Para volver al menu
principal, usar el boton **Regresar al inicio**.

## 4. Productos e inventario

Este modulo permite administrar el catalogo de productos y los movimientos de
stock.

### Buscar productos

1. Escribir el SKU, nombre o marca en el campo **Buscar**.
2. Presionar **Filtrar** o la tecla Enter.
3. Para ver todos los productos otra vez, presionar **Limpiar**.

### Crear un producto

1. Presionar **Nuevo** para limpiar el formulario.
2. Completar los campos: SKU, nombre, marca, costo, precio, stock actual,
   stock minimo y descripcion.
3. Presionar **Guardar producto**.

El SKU y el nombre son obligatorios. El costo, precio y stock no deben ser
negativos.

### Editar un producto

1. Seleccionar un producto en la tabla.
2. Modificar los datos en el formulario.
3. Presionar **Guardar producto**.

Nota: cuando se edita un producto existente, el stock se debe modificar desde
las acciones de inventario, no escribiendo directamente otro stock en el
formulario.

### Desactivar un producto

1. Seleccionar el producto.
2. Presionar **Eliminar**.
3. Confirmar la accion.

El sistema desactiva el producto, no lo borra definitivamente de los archivos.

### Registrar movimientos de inventario

Seleccionar un producto y usar una de estas acciones:

- **Entrada**: aumenta el stock.
- **Salida**: disminuye el stock.
- **Ajuste**: cambia el stock al valor indicado.

Cada movimiento pide cantidad o nuevo stock y un motivo. La tabla de movimientos
muestra el stock anterior, el stock nuevo, el tipo de movimiento, la fecha y el
motivo.

## 5. Ventas

Este modulo permite armar un carrito y registrar ventas completadas.

### Registrar una venta

1. Seleccionar un producto en la lista.
2. Escribir el nombre del cliente.
3. Escribir la cantidad.
4. Presionar **Agregar al carrito**.
5. Repetir el proceso si la venta incluye varios productos.
6. Revisar el total del carrito.
7. Presionar **Registrar venta**.

Al registrar la venta, el sistema descuenta automaticamente el stock de los
productos vendidos y registra movimientos de inventario de tipo **SALIDA**.

### Quitar productos del carrito

1. Seleccionar el producto dentro de la tabla del carrito.
2. Presionar **Quitar item**.

Para vaciar todo el carrito, presionar **Limpiar**.

### Anular una venta

1. Seleccionar una venta en la tabla de ventas registradas.
2. Presionar **Anular venta**.
3. Confirmar la accion.

Cuando se anula una venta, el sistema devuelve el stock al inventario. No se
puede anular una venta que ya tiene factura.

## 6. Facturas

Este modulo permite generar y exportar facturas en PDF.

### Generar una factura

1. Seleccionar una venta pendiente en el campo **Venta pendiente**.
2. Presionar **Generar factura PDF**.
3. Elegir la ubicacion donde se guardara el archivo PDF.

Solo se pueden facturar ventas completadas que aun no tengan factura.

### Ver detalle de una factura

1. Seleccionar una factura en la tabla de facturas emitidas.
2. Presionar **Ver detalle** o simplemente seleccionarla.

El sistema muestra los productos, cantidades, precios unitarios y subtotales.

### Exportar una factura existente

1. Seleccionar una factura ya emitida.
2. Presionar **Exportar PDF**.
3. Elegir la ubicacion del archivo.

## 7. Reportes

Este modulo muestra resumenes de ventas, facturacion y productos.

### Consultar reportes

Se pueden escribir fechas en los campos:

- **Desde**
- **Hasta**

El formato recomendado es:

```text
YYYY-MM-DD
```

Ejemplo:

```text
2026-07-01
```

Luego presionar **Actualizar reportes**.

### Pestanas disponibles

- **Bajo stock**: productos cuyo stock actual esta en el minimo o por debajo.
- **Mas vendidos**: productos con mayor cantidad vendida.
- **Ventas**: listado de ventas registradas.

### Exportar reportes

1. Abrir la pestana del reporte que se quiere exportar.
2. Presionar **Exportar CSV**.
3. Elegir la ubicacion del archivo.

## 8. Recomendaciones de uso

- Ejecutar `crear_db.py` antes de abrir el sistema en una computadora nueva.
- No editar manualmente los archivos de `database/json/` mientras el programa
  esta abierto.
- Hacer copias de seguridad de la carpeta `database/json/` antes de cambios
  importantes.
- Revisar productos en bajo stock antes de registrar muchas ventas.
- Generar la factura solo cuando la venta ya fue revisada, porque una venta con
  factura no se puede anular desde el sistema.

## 9. Problemas comunes

### El sistema no abre

Verificar que se esta ejecutando el comando desde la carpeta principal del
proyecto y que Python este instalado.

### No aparecen productos o datos

Ejecutar:

```powershell
python crear_db.py
```

Esto crea o verifica los archivos JSON iniciales.

### No se puede vender un producto

Revisar que el producto este activo y que tenga stock suficiente.

### No aparece una venta para facturar

La venta puede estar anulada o ya tener una factura generada.

### No se puede anular una venta

Si la venta ya tiene factura, el sistema no permite anularla.
