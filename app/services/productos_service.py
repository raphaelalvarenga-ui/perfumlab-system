from math import ceil

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.categorias_repository import CategoriaRepository
from app.repositories.productos_repository import ProductoRepository
from app.services.exceptions import BadRequestError, ConflictError, NotFoundError


NO_NULOS_PRODUCTO = {
    "sku",
    "nombre",
    "marca",
    "categoria_id",
    "costo",
    "precio",
    "stock_minimo",
    "activo",
}


class ProductosService:
    def __init__(self, db: Session):
        self.db = db
        self.productos_repository = ProductoRepository(db)
        self.categorias_repository = CategoriaRepository(db)

    def listar_productos(
        self,
        *,
        page: int,
        limit: int,
        buscar: str | None = None,
        marca: str | None = None,
        categoria_id: int | None = None,
        genero: str | None = None,
        activo: bool | None = True,
        stock_bajo: bool | None = None,
    ) -> dict:
        items, total = self.productos_repository.list(
            page=page,
            limit=limit,
            buscar=buscar,
            marca=marca,
            categoria_id=categoria_id,
            genero=genero,
            activo=activo,
            stock_bajo=stock_bajo,
        )
        return {
            "items": items,
            "page": page,
            "limit": limit,
            "total": total,
            "pages": ceil(total / limit) if total else 0,
        }

    def obtener_producto(self, producto_id: int):
        producto = self.productos_repository.get_by_id(producto_id)
        if producto is None:
            raise NotFoundError("Producto no encontrado.")
        return producto

    def crear_producto(self, datos: dict):
        self._validar_categoria_activa(datos.get("categoria_id"))
        self._asegurar_sku_disponible(datos["sku"])
        try:
            producto = self.productos_repository.create(datos)
            self.db.commit()
            self.db.refresh(producto)
            return producto
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError("Ya existe un producto con ese SKU.") from error

    def actualizar_producto(self, producto_id: int, datos: dict):
        producto = self.obtener_producto(producto_id)
        self._validar_stock_actual_no_editable(datos)
        self._validar_categoria_activa(datos.get("categoria_id"))
        self._asegurar_sku_disponible(datos["sku"], excluir_id=producto_id)
        try:
            producto = self.productos_repository.update(producto, datos)
            self.db.commit()
            self.db.refresh(producto)
            return producto
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError("Ya existe un producto con ese SKU.") from error

    def actualizar_producto_parcial(self, producto_id: int, datos: dict):
        producto = self.obtener_producto(producto_id)
        if not datos:
            return producto

        self._validar_stock_actual_no_editable(datos)
        self._validar_nulos_no_permitidos(datos)

        if "categoria_id" in datos:
            self._validar_categoria_activa(datos["categoria_id"])
        if "sku" in datos:
            self._asegurar_sku_disponible(datos["sku"], excluir_id=producto_id)

        try:
            producto = self.productos_repository.update(producto, datos)
            self.db.commit()
            self.db.refresh(producto)
            return producto
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError("Ya existe un producto con ese SKU.") from error

    def eliminar_producto(self, producto_id: int):
        producto = self.obtener_producto(producto_id)
        producto = self.productos_repository.soft_delete(producto)
        self.db.commit()
        self.db.refresh(producto)
        return producto

    def _validar_categoria_activa(self, categoria_id: int | None) -> None:
        if categoria_id is None:
            raise BadRequestError("La categoria es obligatoria.")
        categoria = self.categorias_repository.get_by_id(categoria_id)
        if categoria is None:
            raise NotFoundError("La categoria indicada no existe.")
        if not categoria.activo:
            raise BadRequestError(
                "No se puede asociar el producto a una categoria inactiva."
            )

    def _asegurar_sku_disponible(
        self,
        sku: str,
        excluir_id: int | None = None,
    ) -> None:
        existente = self.productos_repository.get_by_sku(sku, excluir_id=excluir_id)
        if existente is not None:
            raise ConflictError("Ya existe un producto con ese SKU.")

    def _validar_nulos_no_permitidos(self, datos: dict) -> None:
        campos_invalidos = sorted(
            campo for campo in NO_NULOS_PRODUCTO if campo in datos and datos[campo] is None
        )
        if campos_invalidos:
            raise BadRequestError(
                "Estos campos no pueden ser nulos: " + ", ".join(campos_invalidos)
            )

    def _validar_stock_actual_no_editable(self, datos: dict) -> None:
        if "stock_actual" in datos:
            raise BadRequestError(
                "El stock_actual solo puede modificarse mediante Inventario."
            )
