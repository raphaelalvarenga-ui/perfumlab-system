from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.orm.acorde import AcordeORM, ProductoAcordeORM
from app.models.orm.nota import NotaORM, ProductoNotaORM
from app.models.orm.producto import ProductoORM


class PerfumeriaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_producto_with_profile(self, producto_id: int) -> ProductoORM | None:
        statement = (
            select(ProductoORM)
            .options(
                selectinload(ProductoORM.acordes_rel).selectinload(
                    ProductoAcordeORM.acorde
                ),
                selectinload(ProductoORM.notas_rel).selectinload(ProductoNotaORM.nota),
            )
            .where(ProductoORM.id == producto_id)
        )
        return self.db.execute(statement).scalar_one_or_none()

    def get_producto_for_update(self, producto_id: int) -> ProductoORM | None:
        statement = select(ProductoORM).where(ProductoORM.id == producto_id).with_for_update()
        return self.db.execute(statement).scalar_one_or_none()

    def get_acordes_by_ids(self, acorde_ids: list[int]) -> list[AcordeORM]:
        if not acorde_ids:
            return []
        statement = select(AcordeORM).where(AcordeORM.id.in_(acorde_ids))
        return list(self.db.execute(statement).scalars())

    def get_notas_by_ids(self, nota_ids: list[int]) -> list[NotaORM]:
        if not nota_ids:
            return []
        statement = select(NotaORM).where(NotaORM.id.in_(nota_ids))
        return list(self.db.execute(statement).scalars())

    def replace_profile(
        self,
        producto_id: int,
        *,
        acordes: list[dict],
        notas: list[dict],
    ) -> None:
        self.db.execute(
            delete(ProductoAcordeORM).where(ProductoAcordeORM.producto_id == producto_id)
        )
        self.db.execute(
            delete(ProductoNotaORM).where(ProductoNotaORM.producto_id == producto_id)
        )
        for item in acordes:
            self.db.add(ProductoAcordeORM(producto_id=producto_id, **item))
        for item in notas:
            self.db.add(ProductoNotaORM(producto_id=producto_id, **item))
        self.db.flush()
