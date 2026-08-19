from app.api_client import get_api_client
from app.database.json_storage import (
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
    def __init__(self, ruta_db=None, api_client=None):
        self.ruta_datos = ruta_db
        self.api = api_client or (get_api_client() if ruta_db is None else None)
        if self._usar_json:
            inicializar_datos_json(self.ruta_datos)

    @property
    def _usar_json(self):
        return self.ruta_datos is not None

    def crear_categoria(self, categoria):
        categoria.validar()
        nombre = categoria.nombre.strip()
        if not self._usar_json:
            creada = self.api.categorias.crear(
                {"nombre": nombre, "activo": bool(categoria.activo)}
            )
            return creada["id"]

        categorias = cargar_tabla("categorias", self.ruta_datos)
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
        if not self._usar_json:
            categorias = self.api.categorias.listar()
            if not incluir_inactivas:
                categorias = [categoria for categoria in categorias if categoria.get("activo")]
            return [Categoria.desde_fila(categoria) for categoria in categorias]

        categorias = cargar_tabla("categorias", self.ruta_datos)
        if not incluir_inactivas:
            categorias = [categoria for categoria in categorias if es_activo(categoria)]
        categorias.sort(key=lambda categoria: categoria["nombre"].lower())
        return [Categoria.desde_fila(categoria) for categoria in categorias]

    def crear_producto(self, producto):
        producto.validar()
        if not self._usar_json:
            creado = self.api.productos.crear(self._payload_producto(producto, include_stock=True))
            return creado["id"]

        productos = cargar_tabla("productos", self.ruta_datos)
        if self._existe_sku_producto(productos, producto.sku):
            raise ValueError("El SKU ya esta registrado.")
        if producto.categoria_id is not None:
            self._validar_categoria(producto.categoria_id)

        producto_id = siguiente_id("productos", productos)
        productos.append(self._crear_registro_producto(producto_id, producto))
        guardar_tabla("productos", productos, self.ruta_datos)
        return producto_id

    def crear_productos_lote(self, productos_nuevos):
        if not productos_nuevos:
            raise ValueError("No hay productos para importar.")
        if not self._usar_json:
            return self._crear_productos_lote_api(productos_nuevos)

        productos = cargar_tabla("productos", self.ruta_datos)
        skus_lote = set()

        for producto in productos_nuevos:
            producto.validar()
            sku_normalizado = producto.sku.strip().lower()
            if sku_normalizado in skus_lote:
                raise ValueError(f"El SKU {producto.sku} esta duplicado en el archivo.")
            if self._existe_sku_producto(productos, producto.sku):
                raise ValueError(f"El SKU {producto.sku} ya esta registrado.")
            if producto.categoria_id is not None:
                self._validar_categoria(producto.categoria_id)
            skus_lote.add(sku_normalizado)

        ids_creados = []
        siguiente_producto_id = siguiente_id("productos", productos)
        for producto in productos_nuevos:
            productos.append(self._crear_registro_producto(siguiente_producto_id, producto))
            ids_creados.append(siguiente_producto_id)
            siguiente_producto_id += 1

        guardar_tabla("productos", productos, self.ruta_datos)
        return ids_creados

    def obtener_producto(self, producto_id):
        if not self._usar_json:
            producto = self.api.productos.obtener(producto_id)
            return Producto.desde_fila(producto)

        productos = cargar_tabla("productos", self.ruta_datos)
        producto = buscar_por_id(productos, producto_id)
        return Producto.desde_fila(producto) if producto else None

    def obtener_perfil_olfativo(self, producto_id):
        if not self._usar_json:
            return self.api.productos.obtener_perfil_olfativo(producto_id)

        raise ValueError(
            "El perfil olfativo solo esta disponible mediante la API REST."
        )

    def listar_productos(self, incluir_inactivos=False):
        if not self._usar_json:
            productos = self.api.productos.listar_todos(
                activo=None if incluir_inactivos else True
            )
            productos.sort(key=lambda producto: producto["nombre"].lower())
            return [Producto.desde_fila(producto) for producto in productos]

        productos = cargar_tabla("productos", self.ruta_datos)
        if not incluir_inactivos:
            productos = [producto for producto in productos if es_activo(producto)]
        productos.sort(key=lambda producto: producto["nombre"].lower())
        return [Producto.desde_fila(producto) for producto in productos]

    def buscar_productos(self, texto, incluir_inactivos=False):
        texto = texto.strip()
        if not self._usar_json:
            productos = self.api.productos.listar_todos(
                buscar=texto,
                activo=None if incluir_inactivos else True,
            )
            productos.sort(key=lambda producto: producto["nombre"].lower())
            return [Producto.desde_fila(producto) for producto in productos]

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
        if not self._usar_json:
            self.api.productos.actualizar(
                producto_id,
                self._payload_producto(producto, include_stock=False),
            )
            return True

        productos = cargar_tabla("productos", self.ruta_datos)
        registro = buscar_por_id(productos, producto_id)
        if registro is None:
            return False
        if self._existe_sku_producto(productos, producto.sku, excluir_id=producto_id):
            raise ValueError("El SKU ya esta registrado.")
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
        if not self._usar_json:
            self.api.productos.eliminar(producto_id)
            return True

        productos = cargar_tabla("productos", self.ruta_datos)
        registro = buscar_por_id(productos, producto_id)
        if registro is None:
            return False
        registro["activo"] = 0
        registro["fecha_actualizacion"] = fecha_actual()
        guardar_tabla("productos", productos, self.ruta_datos)
        return True

    def eliminar_producto_permanente(self, producto_id):
        if not self._usar_json:
            return self.eliminar_producto(producto_id)

        productos = cargar_tabla("productos", self.ruta_datos)
        cantidad_inicial = len(productos)
        productos = [
            producto
            for producto in productos
            if int(producto.get("id", 0)) != int(producto_id)
        ]
        guardar_tabla("productos", productos, self.ruta_datos)
        return len(productos) < cantidad_inicial

    def _crear_productos_lote_api(self, productos_nuevos):
        skus_lote = set()
        skus_existentes = {
            producto["sku"].strip().lower()
            for producto in self.api.productos.listar_todos(activo=None)
            if str(producto.get("sku") or "").strip()
        }
        ids_creados = []
        for producto in productos_nuevos:
            producto.validar()
            sku_normalizado = producto.sku.strip().lower()
            if sku_normalizado in skus_lote:
                raise ValueError(f"El SKU {producto.sku} esta duplicado en el archivo.")
            if sku_normalizado in skus_existentes:
                raise ValueError(f"El SKU {producto.sku} ya esta registrado.")
            skus_lote.add(sku_normalizado)

        for producto in productos_nuevos:
            ids_creados.append(self.crear_producto(producto))
        return ids_creados

    def _payload_producto(self, producto, *, include_stock):
        if producto.categoria_id is None:
            raise ValueError("Seleccione una categoria para el producto.")
        payload = {
            "sku": producto.sku.strip(),
            "nombre": producto.nombre.strip(),
            "categoria_id": int(producto.categoria_id),
            "marca": producto.marca.strip(),
            "descripcion": producto.descripcion.strip() or None,
            "costo": f"{float(producto.costo):.2f}",
            "precio": f"{float(producto.precio):.2f}",
            "stock_minimo": int(producto.stock_minimo),
            "activo": bool(producto.activo),
        }
        if include_stock:
            payload["stock_actual"] = int(producto.stock_actual)
        return payload

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
        if not self._usar_json:
            self.api.categorias.obtener(categoria_id)
            return
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
