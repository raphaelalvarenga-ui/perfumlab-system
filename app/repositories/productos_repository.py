from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.orm.producto import ProductoORM


class ProductoRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, producto_id: int) -> ProductoORM | None:
        return self.db.get(ProductoORM, producto_id)

    def get_by_sku(
        self,
        sku: str,
        excluir_id: int | None = None,
    ) -> ProductoORM | None:
        statement = select(ProductoORM).where(
            func.lower(ProductoORM.sku) == sku.strip().lower()
        )
        if excluir_id is not None:
            statement = statement.where(ProductoORM.id != excluir_id)
        return self.db.execute(statement).scalar_one_or_none()

    def list(
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
    ) -> tuple[list[ProductoORM], int]:
        statement = self._aplicar_filtros(
            select(ProductoORM),
            buscar=buscar,
            marca=marca,
            categoria_id=categoria_id,
            genero=genero,
            activo=activo,
            stock_bajo=stock_bajo,
        )
        count_statement = self._aplicar_filtros(
            select(func.count(ProductoORM.id)),
            buscar=buscar,
            marca=marca,
            categoria_id=categoria_id,
            genero=genero,
            activo=activo,
            stock_bajo=stock_bajo,
        )

        offset = (page - 1) * limit
        items = self.db.execute(
            statement.order_by(ProductoORM.nombre.asc()).offset(offset).limit(limit)
        ).scalars()
        total = self.db.execute(count_statement).scalar_one()
        return list(items), int(total)

    def create(self, datos: dict) -> ProductoORM:
        producto = ProductoORM(**datos)
        self.db.add(producto)
        self.db.flush()
        self.db.refresh(producto)
        return producto

    def update(self, producto: ProductoORM, datos: dict) -> ProductoORM:
        for campo, valor in datos.items():
            setattr(producto, campo, valor)
        self.db.flush()
        self.db.refresh(producto)
        return producto

    def soft_delete(self, producto: ProductoORM) -> ProductoORM:
        producto.activo = False
        self.db.flush()
        self.db.refresh(producto)
        return producto

    def _aplicar_filtros(
        self,
        statement: Select,
        *,
        buscar: str | None,
        marca: str | None,
        categoria_id: int | None,
        genero: str | None,
        activo: bool | None,
        stock_bajo: bool | None,
    ) -> Select:
        if buscar:
            patron = f"%{buscar.strip()}%"
            statement = statement.where(
                or_(
                    ProductoORM.nombre.ilike(patron),
                    ProductoORM.sku.ilike(patron),
                    ProductoORM.marca.ilike(patron),
                )
            )
        if marca:
            statement = statement.where(ProductoORM.marca.ilike(f"%{marca.strip()}%"))
        if categoria_id is not None:
            statement = statement.where(ProductoORM.categoria_id == categoria_id)
        if genero:
            statement = statement.where(ProductoORM.genero.ilike(f"%{genero.strip()}%"))
        if activo is not None:
            statement = statement.where(ProductoORM.activo == activo)
        if stock_bajo is True:
            statement = statement.where(
                ProductoORM.stock_actual <= ProductoORM.stock_minimo
            )
        elif stock_bajo is False:
            statement = statement.where(
                ProductoORM.stock_actual > ProductoORM.stock_minimo
            )
        return statement
