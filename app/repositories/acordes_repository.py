from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.orm.acorde import AcordeORM


class AcordesRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, acorde_id: int) -> AcordeORM | None:
        return self.db.get(AcordeORM, acorde_id)

    def get_by_slug(self, slug: str, excluir_id: int | None = None) -> AcordeORM | None:
        statement = select(AcordeORM).where(
            func.lower(AcordeORM.slug) == slug.strip().lower()
        )
        if excluir_id is not None:
            statement = statement.where(AcordeORM.id != excluir_id)
        return self.db.execute(statement).scalar_one_or_none()

    def list(
        self,
        *,
        page: int,
        limit: int,
        buscar: str | None = None,
        activo: bool | None = True,
    ) -> tuple[list[AcordeORM], int]:
        statement = self._aplicar_filtros(select(AcordeORM), buscar=buscar, activo=activo)
        count_statement = self._aplicar_filtros(
            select(func.count(AcordeORM.id)),
            buscar=buscar,
            activo=activo,
        )
        offset = (page - 1) * limit
        items = self.db.execute(
            statement.order_by(AcordeORM.nombre.asc()).offset(offset).limit(limit)
        ).scalars()
        total = self.db.execute(count_statement).scalar_one()
        return list(items), int(total)

    def create(self, datos: dict) -> AcordeORM:
        acorde = AcordeORM(**datos)
        self.db.add(acorde)
        self.db.flush()
        self.db.refresh(acorde)
        return acorde

    def update(self, acorde: AcordeORM, datos: dict) -> AcordeORM:
        for campo, valor in datos.items():
            setattr(acorde, campo, valor)
        self.db.flush()
        self.db.refresh(acorde)
        return acorde

    def soft_delete(self, acorde: AcordeORM) -> AcordeORM:
        acorde.activo = False
        self.db.flush()
        self.db.refresh(acorde)
        return acorde

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
                or_(AcordeORM.nombre.ilike(patron), AcordeORM.slug.ilike(patron))
            )
        if activo is not None:
            statement = statement.where(AcordeORM.activo == activo)
        return statement
