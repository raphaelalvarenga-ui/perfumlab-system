from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, validate_password_policy
from app.models.orm.usuario import UsuarioORM
from app.models.tipos import RolUsuario
from app.repositories.usuarios_repository import UsuariosRepository
from app.schemas.usuario import UsuarioListResponse
from app.services.exceptions import BadRequestError, ConflictError, NotFoundError


class UsuariosService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UsuariosRepository(db)

    def crear_usuario(self, datos: dict) -> UsuarioORM:
        datos_limpios = dict(datos)
        password = datos_limpios.pop("password")
        self._asegurar_username_disponible(datos_limpios["username"])
        self._asegurar_email_disponible(datos_limpios.get("email"))
        datos_limpios["password_hash"] = hash_password(password)
        datos_limpios["token_version"] = 0

        try:
            usuario = self.repository.create(datos_limpios)
            self.db.commit()
            self.db.refresh(usuario)
            return usuario
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError("Ya existe un usuario con ese username o email.") from error

    def listar_usuarios(
        self,
        *,
        page: int,
        limit: int,
        buscar: str | None = None,
        rol: RolUsuario | None = None,
        activo: bool | None = True,
    ) -> UsuarioListResponse:
        items, total = self.repository.list(
            page=page,
            limit=limit,
            buscar=buscar,
            rol=rol,
            activo=activo,
        )
        return UsuarioListResponse.from_items(
            items=items,
            page=page,
            limit=limit,
            total=total,
        )

    def obtener_usuario(self, usuario_id: int) -> UsuarioORM:
        usuario = self.repository.get_by_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuario no encontrado.")
        return usuario

    def actualizar_usuario(self, usuario_id: int, datos: dict) -> UsuarioORM:
        datos_limpios = dict(datos)
        if "password" in datos_limpios or "password_hash" in datos_limpios:
            raise BadRequestError("La contrasena se actualiza en un endpoint separado.")

        try:
            usuario = self.repository.get_by_id_for_update(usuario_id)
            if usuario is None:
                raise NotFoundError("Usuario no encontrado.")
            if not datos_limpios:
                return usuario

            if "username" in datos_limpios:
                self._asegurar_username_disponible(
                    datos_limpios["username"],
                    excluir_id=usuario.id,
                )
            if "email" in datos_limpios:
                self._asegurar_email_disponible(
                    datos_limpios["email"],
                    excluir_id=usuario.id,
                )

            self._proteger_ultimo_admin_si_aplica(usuario, datos_limpios)
            usuario = self.repository.update(usuario, datos_limpios)
            self.db.commit()
            self.db.refresh(usuario)
            return usuario
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError("Ya existe un usuario con ese username o email.") from error
        except Exception:
            self.db.rollback()
            raise

    def desactivar_usuario(self, usuario_id: int) -> UsuarioORM:
        return self.actualizar_usuario(usuario_id, {"activo": False})

    def reset_password(self, usuario_id: int, password_nueva: str) -> UsuarioORM:
        try:
            usuario = self.repository.get_by_id_for_update(usuario_id)
            if usuario is None:
                raise NotFoundError("Usuario no encontrado.")

            validate_password_policy(password_nueva)
            usuario = self.repository.update_password_hash(
                usuario,
                hash_password(password_nueva),
            )
            self.db.commit()
            self.db.refresh(usuario)
            return usuario
        except Exception:
            self.db.rollback()
            raise

    def _asegurar_username_disponible(
        self,
        username: str,
        excluir_id: int | None = None,
    ) -> None:
        if self.repository.get_by_username(username, excluir_id=excluir_id) is not None:
            raise ConflictError("Ya existe un usuario con ese username.")

    def _asegurar_email_disponible(
        self,
        email: str | None,
        excluir_id: int | None = None,
    ) -> None:
        if not email:
            return
        if self.repository.get_by_email(email, excluir_id=excluir_id) is not None:
            raise ConflictError("Ya existe un usuario con ese email.")

    def _proteger_ultimo_admin_si_aplica(
        self,
        usuario: UsuarioORM,
        datos: dict,
    ) -> None:
        if not usuario.activo or usuario.rol != RolUsuario.ADMINISTRADOR:
            return

        nuevo_activo = datos.get("activo", usuario.activo)
        nuevo_rol = datos.get("rol", usuario.rol)
        deja_de_ser_admin_activo = (
            nuevo_activo is False or nuevo_rol != RolUsuario.ADMINISTRADOR
        )
        if not deja_de_ser_admin_activo:
            return

        active_admins = self.repository.active_admins_for_update()
        if len(active_admins) <= 1:
            raise ConflictError("No se puede dejar el sistema sin administradores activos.")
