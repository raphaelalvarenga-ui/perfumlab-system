from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.slug import generar_slug
from app.repositories.notas_repository import NotasRepository
from app.schemas.nota import NotaListResponse
from app.services.exceptions import BadRequestError, ConflictError, NotFoundError


class NotasService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = NotasRepository(db)

    def listar_notas(
        self,
        *,
        page: int,
        limit: int,
        buscar: str | None = None,
        activo: bool | None = True,
    ) -> NotaListResponse:
        items, total = self.repository.list(
            page=page,
            limit=limit,
            buscar=buscar,
            activo=activo,
        )
        return NotaListResponse.from_items(
            items=items,
            page=page,
            limit=limit,
            total=total,
        )

    def obtener_nota(self, nota_id: int):
        nota = self.repository.get_by_id(nota_id)
        if nota is None:
            raise NotFoundError("Nota no encontrada.")
        return nota

    def crear_nota(self, datos: dict):
        datos_limpios = self._preparar_datos(datos)
        self._asegurar_slug_disponible(datos_limpios["slug"])
        try:
            nota = self.repository.create(datos_limpios)
            self.db.commit()
            self.db.refresh(nota)
            return nota
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError("Ya existe una nota con ese slug.") from error

    def actualizar_nota(self, nota_id: int, datos: dict):
        nota = self.obtener_nota(nota_id)
        if not datos:
            return nota
        datos_limpios = self._preparar_datos(datos, parcial=True)
        if "slug" in datos_limpios:
            self._asegurar_slug_disponible(datos_limpios["slug"], excluir_id=nota_id)
        try:
            nota = self.repository.update(nota, datos_limpios)
            self.db.commit()
            self.db.refresh(nota)
            return nota
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError("Ya existe una nota con ese slug.") from error

    def eliminar_nota(self, nota_id: int):
        nota = self.obtener_nota(nota_id)
        nota = self.repository.soft_delete(nota)
        self.db.commit()
        self.db.refresh(nota)
        return nota

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
            raise ConflictError("Ya existe una nota con ese slug.")
