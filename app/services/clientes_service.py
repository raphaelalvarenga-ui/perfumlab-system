from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.clientes_repository import ClienteRepository
from app.schemas.cliente import ClienteListResponse
from app.services.exceptions import BadRequestError, ConflictError, NotFoundError


NO_NULOS_CLIENTE = {"nombre", "activo"}


class ClientesService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = ClienteRepository(db)

    def listar_clientes(
        self,
        *,
        page: int,
        limit: int,
        buscar: str | None = None,
        activo: bool | None = True,
    ) -> ClienteListResponse:
        items, total = self.repository.list(
            page=page,
            limit=limit,
            buscar=buscar,
            activo=activo,
        )
        return ClienteListResponse.from_items(
            items=items,
            page=page,
            limit=limit,
            total=total,
        )

    def obtener_cliente(self, cliente_id: int):
        cliente = self.repository.get_by_id(cliente_id)
        if cliente is None:
            raise NotFoundError("Cliente no encontrado.")
        return cliente

    def crear_cliente(self, datos: dict):
        self._asegurar_correo_disponible(datos.get("correo"))
        try:
            cliente = self.repository.create(datos)
            self.db.commit()
            self.db.refresh(cliente)
            return cliente
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError("Ya existe un cliente con ese correo.") from error

    def actualizar_cliente(self, cliente_id: int, datos: dict):
        cliente = self.obtener_cliente(cliente_id)
        self._asegurar_correo_disponible(
            datos.get("correo"),
            excluir_id=cliente_id,
        )
        try:
            cliente = self.repository.update(cliente, datos)
            self.db.commit()
            self.db.refresh(cliente)
            return cliente
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError("Ya existe un cliente con ese correo.") from error

    def actualizar_cliente_parcial(self, cliente_id: int, datos: dict):
        cliente = self.obtener_cliente(cliente_id)
        if not datos:
            return cliente

        self._validar_nulos_no_permitidos(datos)

        if "correo" in datos:
            self._asegurar_correo_disponible(
                datos.get("correo"),
                excluir_id=cliente_id,
            )

        try:
            cliente = self.repository.update(cliente, datos)
            self.db.commit()
            self.db.refresh(cliente)
            return cliente
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError("Ya existe un cliente con ese correo.") from error

    def eliminar_cliente(self, cliente_id: int):
        cliente = self.obtener_cliente(cliente_id)
        cliente = self.repository.soft_delete(cliente)
        self.db.commit()
        self.db.refresh(cliente)
        return cliente

    def _asegurar_correo_disponible(
        self,
        correo: str | None,
        excluir_id: int | None = None,
    ) -> None:
        existente = self.repository.get_by_email(correo, excluir_id=excluir_id)
        if existente is not None:
            raise ConflictError("Ya existe un cliente con ese correo.")

    def _validar_nulos_no_permitidos(self, datos: dict) -> None:
        campos_invalidos = sorted(
            campo for campo in NO_NULOS_CLIENTE if campo in datos and datos[campo] is None
        )
        if campos_invalidos:
            raise BadRequestError(
                "Estos campos no pueden ser nulos: " + ", ".join(campos_invalidos)
            )
