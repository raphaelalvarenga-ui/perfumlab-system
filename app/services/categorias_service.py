from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.categorias_repository import CategoriaRepository
from app.services.exceptions import ConflictError, NotFoundError


class CategoriasService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = CategoriaRepository(db)

    def listar_categorias(self) -> list:
        return self.repository.list(activo=True)

    def obtener_categoria(self, categoria_id: int):
        categoria = self.repository.get_by_id(categoria_id)
        if categoria is None:
            raise NotFoundError("Categoria no encontrada.")
        return categoria

    def crear_categoria(self, datos: dict):
        self._asegurar_nombre_disponible(datos["nombre"])
        try:
            categoria = self.repository.create(datos)
            self.db.commit()
            self.db.refresh(categoria)
            return categoria
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError("Ya existe una categoria con ese nombre.") from error

    def actualizar_categoria(self, categoria_id: int, datos: dict):
        categoria = self.obtener_categoria(categoria_id)
        self._asegurar_nombre_disponible(datos["nombre"], excluir_id=categoria_id)
        try:
            categoria = self.repository.update(categoria, datos)
            self.db.commit()
            self.db.refresh(categoria)
            return categoria
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError("Ya existe una categoria con ese nombre.") from error

    def actualizar_categoria_parcial(self, categoria_id: int, datos: dict):
        categoria = self.obtener_categoria(categoria_id)
        if not datos:
            return categoria
        if "nombre" in datos:
            self._asegurar_nombre_disponible(
                datos["nombre"],
                excluir_id=categoria_id,
            )
        try:
            categoria = self.repository.update(categoria, datos)
            self.db.commit()
            self.db.refresh(categoria)
            return categoria
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError("Ya existe una categoria con ese nombre.") from error

    def eliminar_categoria(self, categoria_id: int):
        categoria = self.obtener_categoria(categoria_id)
        categoria = self.repository.soft_delete(categoria)
        self.db.commit()
        self.db.refresh(categoria)
        return categoria

    def _asegurar_nombre_disponible(
        self,
        nombre: str,
        excluir_id: int | None = None,
    ) -> None:
        existente = self.repository.get_by_nombre(nombre, excluir_id=excluir_id)
        if existente is not None:
            raise ConflictError("Ya existe una categoria con ese nombre.")
