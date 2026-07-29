from app.database.json_storage import (
    DATABASE_PATH,
    buscar_por_id,
    cargar_tabla,
    coincide_texto,
    es_activo,
    fecha_actual,
    guardar_tabla,
    inicializar_datos_json,
    siguiente_id,
)
from app.models.categoria import Categoria
from app.models.producto import Producto


class ProductosController:
    def __init__(self, ruta_db=DATABASE_PATH):
        self.ruta_datos = ruta_db
        inicializar_datos_json(self.ruta_datos)

    def crear_categoria(self, categoria):
        categoria.validar()
        categorias = cargar_tabla("categorias", self.ruta_datos)
        nombre = categoria.nombre.strip()

        if self._existe_nombre_categoria(categorias, nombre):
            raise ValueError("Ya existe una categoria con ese nombre.")

        categoria_id = siguiente_id("categorias", categorias)
        categorias.append(
            {
                "id": categoria_id,
                "nombre": nombre,
                "descripcion": categoria.descripcion.strip(),
                "activo": int(categoria.activo),
                "fecha_creacion": fecha_actual(),
                "fecha_actualizacion": None,
            }
        )
        guardar_tabla("categorias", categorias, self.ruta_datos)
        return categoria_id

    def listar_categorias(self, incluir_inactivas=False):
        categorias = cargar_tabla("categorias", self.ruta_datos)

        if not incluir_inactivas:
            categorias = [categoria for categoria in categorias if es_activo(categoria)]

        categorias.sort(key=lambda categoria: categoria["nombre"].lower())
        return [Categoria.desde_fila(categoria) for categoria in categorias]

    def crear_producto(self, producto):
        producto.validar()
        productos = cargar_tabla("productos", self.ruta_datos)

        if self._existe_sku_producto(productos, producto.sku):
            raise ValueError("Ya existe un producto con ese SKU.")

        if producto.categoria_id is not None:
            self._validar_categoria(producto.categoria_id)

        producto_id = siguiente_id("productos", productos)
        productos.append(self._crear_registro_producto(producto_id, producto))
        guardar_tabla("productos", productos, self.ruta_datos)
        return producto_id

    def obtener_producto(self, producto_id):
        productos = cargar_tabla("productos", self.ruta_datos)
        producto = buscar_por_id(productos, producto_id)
        return Producto.desde_fila(producto) if producto else None

    def listar_productos(self, incluir_inactivos=False):
        productos = cargar_tabla("productos", self.ruta_datos)

        if not incluir_inactivos:
            productos = [producto for producto in productos if es_activo(producto)]

        productos.sort(key=lambda producto: producto["nombre"].lower())
        return [Producto.desde_fila(producto) for producto in productos]

    def buscar_productos(self, texto, incluir_inactivos=False):
        texto = texto.strip()
        productos = cargar_tabla("productos", self.ruta_datos)

        if not incluir_inactivos:
            productos = [producto for producto in productos if es_activo(producto)]

        productos = [
            producto
            for producto in productos
            if (
                coincide_texto(producto.get("sku"), texto)
                or coincide_texto(producto.get("nombre"), texto)
                or coincide_texto(producto.get("marca"), texto)
            )
        ]
        productos.sort(key=lambda producto: producto["nombre"].lower())
        return [Producto.desde_fila(producto) for producto in productos]

    def actualizar_producto(self, producto_id, producto):
        producto.validar()
        productos = cargar_tabla("productos", self.ruta_datos)
        registro = buscar_por_id(productos, producto_id)

        if registro is None:
            return False

        if self._existe_sku_producto(productos, producto.sku, excluir_id=producto_id):
            raise ValueError("Ya existe un producto con ese SKU.")

        if producto.categoria_id is not None:
            self._validar_categoria(producto.categoria_id)

        registro.update(
            {
                "sku": producto.sku.strip(),
                "nombre": producto.nombre.strip(),
                "categoria_id": producto.categoria_id,
                "marca": producto.marca.strip(),
                "descripcion": producto.descripcion.strip(),
                "costo": float(producto.costo),
                "precio": float(producto.precio),
                "stock_actual": int(producto.stock_actual),
                "stock_minimo": int(producto.stock_minimo),
                "activo": int(producto.activo),
                "fecha_actualizacion": fecha_actual(),
            }
        )
        guardar_tabla("productos", productos, self.ruta_datos)
        return True

    def eliminar_producto(self, producto_id):
        productos = cargar_tabla("productos", self.ruta_datos)
        registro = buscar_por_id(productos, producto_id)

        if registro is None:
            return False

        registro["activo"] = 0
        registro["fecha_actualizacion"] = fecha_actual()
        guardar_tabla("productos", productos, self.ruta_datos)
        return True

    def eliminar_producto_permanente(self, producto_id):
        productos = cargar_tabla("productos", self.ruta_datos)
        cantidad_inicial = len(productos)
        productos = [
            producto
            for producto in productos
            if int(producto.get("id", 0)) != int(producto_id)
        ]
        guardar_tabla("productos", productos, self.ruta_datos)
        return len(productos) < cantidad_inicial

    def _crear_registro_producto(self, producto_id, producto):
        return {
            "id": producto_id,
            "sku": producto.sku.strip(),
            "nombre": producto.nombre.strip(),
            "categoria_id": producto.categoria_id,
            "marca": producto.marca.strip(),
            "descripcion": producto.descripcion.strip(),
            "costo": float(producto.costo),
            "precio": float(producto.precio),
            "stock_actual": int(producto.stock_actual),
            "stock_minimo": int(producto.stock_minimo),
            "ml": getattr(producto, "ml", 50),
            "imagen": getattr(producto, "imagen", None),
            "activo": int(producto.activo),
            "fecha_creacion": fecha_actual(),
            "fecha_actualizacion": None,
        }

    def _validar_categoria(self, categoria_id):
        categorias = cargar_tabla("categorias", self.ruta_datos)
        categoria = buscar_por_id(categorias, categoria_id)

        if categoria is None:
            raise ValueError("La categoria indicada no existe.")

    def _existe_nombre_categoria(self, categorias, nombre):
        nombre = nombre.strip().lower()
        return any(categoria["nombre"].strip().lower() == nombre for categoria in categorias)

    def _existe_sku_producto(self, productos, sku, excluir_id=None):
        sku = sku.strip().lower()
        excluir_id = int(excluir_id) if excluir_id is not None else None

        return any(
            producto["sku"].strip().lower() == sku
            and int(producto["id"]) != excluir_id
            for producto in productos
        )
