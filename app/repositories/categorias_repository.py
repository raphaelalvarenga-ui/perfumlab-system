from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.orm.categoria import CategoriaORM


class CategoriaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, categoria_id: int) -> CategoriaORM | None:
        return self.db.get(CategoriaORM, categoria_id)

    def get_by_nombre(
        self,
        nombre: str,
        excluir_id: int | None = None,
    ) -> CategoriaORM | None:
        statement = select(CategoriaORM).where(
            func.lower(CategoriaORM.nombre) == nombre.strip().lower()
        )
        if excluir_id is not None:
            statement = statement.where(CategoriaORM.id != excluir_id)
        return self.db.execute(statement).scalar_one_or_none()

    def list(self, activo: bool = True) -> list[CategoriaORM]:
        statement = select(CategoriaORM).order_by(CategoriaORM.nombre.asc())
        if activo is not None:
            statement = statement.where(CategoriaORM.activo == activo)
        return list(self.db.execute(statement).scalars())

    def create(self, datos: dict) -> CategoriaORM:
        categoria = CategoriaORM(**datos)
        self.db.add(categoria)
        self.db.flush()
        self.db.refresh(categoria)
        return categoria

    def update(self, categoria: CategoriaORM, datos: dict) -> CategoriaORM:
        for campo, valor in datos.items():
            setattr(categoria, campo, valor)
        self.db.flush()
        self.db.refresh(categoria)
        return categoria

    def soft_delete(self, categoria: CategoriaORM) -> CategoriaORM:
        categoria.activo = False
        self.db.flush()
        self.db.refresh(categoria)
        return categoria
