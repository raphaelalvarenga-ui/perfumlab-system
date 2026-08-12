from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.orm.cliente import ClienteORM


class ClienteRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, cliente_id: int) -> ClienteORM | None:
        return self.db.get(ClienteORM, cliente_id)

    def get_by_email(
        self,
        correo: str | None,
        excluir_id: int | None = None,
    ) -> ClienteORM | None:
        if not correo:
            return None

        statement = select(ClienteORM).where(
            func.lower(ClienteORM.correo) == correo.strip().lower()
        )
        if excluir_id is not None:
            statement = statement.where(ClienteORM.id != excluir_id)
        return self.db.execute(statement).scalar_one_or_none()

    def list(
        self,
        *,
        page: int,
        limit: int,
        buscar: str | None = None,
        activo: bool | None = True,
    ) -> tuple[list[ClienteORM], int]:
        statement = self._aplicar_filtros(
            select(ClienteORM),
            buscar=buscar,
            activo=activo,
        )
        count_statement = self._aplicar_filtros(
            select(func.count(ClienteORM.id)),
            buscar=buscar,
            activo=activo,
        )

        offset = (page - 1) * limit
        items = self.db.execute(
            statement.order_by(ClienteORM.nombre.asc()).offset(offset).limit(limit)
        ).scalars()
        total = self.db.execute(count_statement).scalar_one()
        return list(items), int(total)

    def create(self, datos: dict) -> ClienteORM:
        cliente = ClienteORM(**datos)
        self.db.add(cliente)
        self.db.flush()
        self.db.refresh(cliente)
        return cliente

    def update(self, cliente: ClienteORM, datos: dict) -> ClienteORM:
        for campo, valor in datos.items():
            setattr(cliente, campo, valor)
        self.db.flush()
        self.db.refresh(cliente)
        return cliente

    def soft_delete(self, cliente: ClienteORM) -> ClienteORM:
        cliente.activo = False
        self.db.flush()
        self.db.refresh(cliente)
        return cliente

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
                or_(
                    ClienteORM.nombre.ilike(patron),
                    ClienteORM.correo.ilike(patron),
                    ClienteORM.telefono.ilike(patron),
                )
            )
        if activo is not None:
            statement = statement.where(ClienteORM.activo == activo)
        return statement
