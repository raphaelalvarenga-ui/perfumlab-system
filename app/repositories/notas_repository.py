from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.orm.nota import NotaORM


class NotasRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, nota_id: int) -> NotaORM | None:
        return self.db.get(NotaORM, nota_id)

    def get_by_slug(self, slug: str, excluir_id: int | None = None) -> NotaORM | None:
        statement = select(NotaORM).where(func.lower(NotaORM.slug) == slug.strip().lower())
        if excluir_id is not None:
            statement = statement.where(NotaORM.id != excluir_id)
        return self.db.execute(statement).scalar_one_or_none()

    def list(
        self,
        *,
        page: int,
        limit: int,
        buscar: str | None = None,
        activo: bool | None = True,
    ) -> tuple[list[NotaORM], int]:
        statement = self._aplicar_filtros(select(NotaORM), buscar=buscar, activo=activo)
        count_statement = self._aplicar_filtros(
            select(func.count(NotaORM.id)),
            buscar=buscar,
            activo=activo,
        )
        offset = (page - 1) * limit
        items = self.db.execute(
            statement.order_by(NotaORM.nombre.asc()).offset(offset).limit(limit)
        ).scalars()
        total = self.db.execute(count_statement).scalar_one()
        return list(items), int(total)

    def create(self, datos: dict) -> NotaORM:
        nota = NotaORM(**datos)
        self.db.add(nota)
        self.db.flush()
        self.db.refresh(nota)
        return nota

    def update(self, nota: NotaORM, datos: dict) -> NotaORM:
        for campo, valor in datos.items():
            setattr(nota, campo, valor)
        self.db.flush()
        self.db.refresh(nota)
        return nota

    def soft_delete(self, nota: NotaORM) -> NotaORM:
        nota.activo = False
        self.db.flush()
        self.db.refresh(nota)
        return nota

    def _aplicar_filtros(
        self,
        statement: Select,
        *,
        buscar: str | None,
        activo: bool | None,
    ) -> Select:
        if buscar:
            patron = f"%{buscar.strip()}%"
            statement = statement.where(
                or_(NotaORM.nombre.ilike(patron), NotaORM.slug.ilike(patron))
            )
        if activo is not None:
            statement = statement.where(NotaORM.activo == activo)
        return statement
