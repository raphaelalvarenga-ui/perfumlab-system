from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.orm.usuario import UsuarioORM
from app.models.tipos import RolUsuario


class UsuariosRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, usuario_id: int) -> UsuarioORM | None:
        return self.db.get(UsuarioORM, usuario_id)

    def get_by_id_for_update(self, usuario_id: int) -> UsuarioORM | None:
        statement = select(UsuarioORM).where(UsuarioORM.id == usuario_id).with_for_update()
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_username(
        self,
        username: str,
        excluir_id: int | None = None,
    ) -> UsuarioORM | None:
        statement = select(UsuarioORM).where(
            func.lower(UsuarioORM.username) == username.strip().lower()
        )
        if excluir_id is not None:
            statement = statement.where(UsuarioORM.id != excluir_id)
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_email(
        self,
        email: str,
        excluir_id: int | None = None,
    ) -> UsuarioORM | None:
        statement = select(UsuarioORM).where(
            func.lower(UsuarioORM.email) == email.strip().lower()
        )
        if excluir_id is not None:
            statement = statement.where(UsuarioORM.id != excluir_id)
        return self.db.execute(statement).scalar_one_or_none()

    def list(
        self,
        *,
        page: int,
        limit: int,
        buscar: str | None = None,
        rol: RolUsuario | None = None,
        activo: bool | None = True,
    ) -> tuple[list[UsuarioORM], int]:
        statement = self._aplicar_filtros(
            select(UsuarioORM),
            buscar=buscar,
            rol=rol,
            activo=activo,
        )
        count_statement = self._aplicar_filtros(
            select(func.count(UsuarioORM.id)),
            buscar=buscar,
            rol=rol,
            activo=activo,
        )
        offset = (page - 1) * limit
        items = self.db.execute(
            statement.order_by(UsuarioORM.id.asc()).offset(offset).limit(limit)
        ).scalars()
        total = self.db.execute(count_statement).scalar_one()
        return list(items), int(total)

    def create(self, datos: dict) -> UsuarioORM:
        usuario = UsuarioORM(**datos)
        self.db.add(usuario)
        self.db.flush()
        self.db.refresh(usuario)
        return usuario

    def update(self, usuario: UsuarioORM, datos: dict) -> UsuarioORM:
        for campo, valor in datos.items():
            setattr(usuario, campo, valor)
        self.db.flush()
        self.db.refresh(usuario)
        return usuario

    def set_last_login(self, usuario: UsuarioORM, last_login_at: datetime) -> UsuarioORM:
        usuario.last_login_at = last_login_at
        self.db.flush()
        self.db.refresh(usuario)
        return usuario

    def update_password_hash(self, usuario: UsuarioORM, password_hash: str) -> UsuarioORM:
        usuario.password_hash = password_hash
        usuario.token_version += 1
        self.db.flush()
        self.db.refresh(usuario)
        return usuario

    def active_admins_for_update(self) -> list[UsuarioORM]:
        statement = (
            select(UsuarioORM)
            .where(
                UsuarioORM.activo.is_(True),
                UsuarioORM.rol == RolUsuario.ADMINISTRADOR,
            )
            .order_by(UsuarioORM.id.asc())
            .with_for_update()
        )
        return list(self.db.execute(statement).scalars())

    def count_active_admins(self) -> int:
        statement = select(func.count(UsuarioORM.id)).where(
            UsuarioORM.activo.is_(True),
            UsuarioORM.rol == RolUsuario.ADMINISTRADOR,
        )
        return int(self.db.execute(statement).scalar_one() or 0)

    def _aplicar_filtros(
        self,
        statement: Select,
        *,
        buscar: str | None,
        rol: RolUsuario | None,
        activo: bool | None,
    ) -> Select:
        if buscar:
            patron = f"%{buscar.strip()}%"
            statement = statement.where(
                or_(
                    UsuarioORM.nombre.ilike(patron),
                    UsuarioORM.username.ilike(patron),
                    UsuarioORM.email.ilike(patron),
                )
            )
        if rol is not None:
            statement = statement.where(UsuarioORM.rol == rol)
        if activo is not None:
            statement = statement.where(UsuarioORM.activo == activo)
        return statement
