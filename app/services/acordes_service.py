from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.slug import generar_slug
from app.repositories.acordes_repository import AcordesRepository
from app.schemas.acorde import AcordeListResponse
from app.services.exceptions import BadRequestError, ConflictError, NotFoundError


class AcordesService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = AcordesRepository(db)

    def listar_acordes(
        self,
        *,
        page: int,
        limit: int,
        buscar: str | None = None,
        activo: bool | None = True,
    ) -> AcordeListResponse:
        items, total = self.repository.list(
            page=page,
            limit=limit,
            buscar=buscar,
            activo=activo,
        )
        return AcordeListResponse.from_items(
            items=items,
            page=page,
            limit=limit,
            total=total,
        )

    def obtener_acorde(self, acorde_id: int):
        acorde = self.repository.get_by_id(acorde_id)
        if acorde is None:
            raise NotFoundError("Acorde no encontrado.")
        return acorde

    def crear_acorde(self, datos: dict):
        datos_limpios = self._preparar_datos(datos)
        self._asegurar_slug_disponible(datos_limpios["slug"])
        try:
            acorde = self.repository.create(datos_limpios)
            self.db.commit()
            self.db.refresh(acorde)
            return acorde
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError("Ya existe un acorde con ese slug.") from error

    def actualizar_acorde(self, acorde_id: int, datos: dict):
        acorde = self.obtener_acorde(acorde_id)
        if not datos:
            return acorde
        datos_limpios = self._preparar_datos(datos, parcial=True)
        if "slug" in datos_limpios:
            self._asegurar_slug_disponible(datos_limpios["slug"], excluir_id=acorde_id)
        try:
            acorde = self.repository.update(acorde, datos_limpios)
            self.db.commit()
            self.db.refresh(acorde)
            return acorde
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError("Ya existe un acorde con ese slug.") from error

    def eliminar_acorde(self, acorde_id: int):
        acorde = self.obtener_acorde(acorde_id)
        acorde = self.repository.soft_delete(acorde)
        self.db.commit()
        self.db.refresh(acorde)
        return acorde

    def _preparar_datos(self, datos: dict, *, parcial: bool = False) -> dict:
        datos_limpios = dict(datos)
        if "nombre" in datos_limpios and (
            "slug" not in datos_limpios or datos_limpios.get("slug") is None
        ):
            datos_limpios["slug"] = generar_slug(datos_limpios["nombre"])
        elif parcial and datos_limpios.get("slug") is None:
            datos_limpios.pop("slug", None)
        if not parcial and not datos_limpios.get("slug"):
            raise BadRequestError("El slug es obligatorio.")
        return datos_limpios

    def _asegurar_slug_disponible(
        self,
        slug: str,
        excluir_id: int | None = None,
    ) -> None:
        if self.repository.get_by_slug(slug, excluir_id=excluir_id) is not None:
            raise ConflictError("Ya existe un acorde con ese slug.")
