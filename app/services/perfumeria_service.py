from sqlalchemy.orm import Session

from app.models.orm.producto import ProductoORM
from app.models.tipos import TipoNota
from app.repositories.perfumeria_repository import PerfumeriaRepository
from app.schemas.perfumeria import (
    PerfilOlfativoResponse,
    ProductoAcordeResponse,
    ProductoNotasAgrupadas,
    ProductoNotaResponse,
)
from app.services.exceptions import ConflictError, NotFoundError


class PerfumeriaService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = PerfumeriaRepository(db)

    def obtener_perfil(self, producto_id: int) -> PerfilOlfativoResponse:
        producto = self.repository.get_producto_with_profile(producto_id)
        if producto is None:
            raise NotFoundError("Producto no encontrado.")
        return self._to_response(producto)

    def reemplazar_perfil(
        self,
        producto_id: int,
        datos: dict,
    ) -> PerfilOlfativoResponse:
        try:
            producto = self.repository.get_producto_for_update(producto_id)
            if producto is None:
                raise NotFoundError("Producto no encontrado.")
            if not producto.activo:
                raise ConflictError(
                    "No se puede modificar el perfil olfativo de un producto inactivo."
                )

            acordes_payload = datos.get("acordes") or []
            notas_payload = datos.get("notas") or []
            self._validar_acordes(acordes_payload)
            self._validar_notas(notas_payload)

            self.repository.replace_profile(
                producto_id,
                acordes=[
                    {
                        "acorde_id": item["acorde_id"],
                        "intensidad": item.get("intensidad"),
                        "posicion": item.get("posicion"),
                    }
                    for item in acordes_payload
                ],
                notas=[
                    {
                        "nota_id": item["nota_id"],
                        "tipo": item["tipo"],
                        "posicion": item.get("posicion"),
                    }
                    for item in notas_payload
                ],
            )
            self.db.commit()
            return self.obtener_perfil(producto_id)
        except Exception:
            self.db.rollback()
            raise

    def _validar_acordes(self, items: list[dict]) -> None:
        acorde_ids = [item["acorde_id"] for item in items]
        if len(set(acorde_ids)) != len(acorde_ids):
            raise ConflictError("El perfil no puede repetir acordes.")

        acordes = {acorde.id: acorde for acorde in self.repository.get_acordes_by_ids(acorde_ids)}
        faltantes = sorted(set(acorde_ids) - set(acordes))
        if faltantes:
            raise NotFoundError("Acorde no encontrado.")
        if any(not acorde.activo for acorde in acordes.values()):
            raise ConflictError("No se puede usar un acorde inactivo.")

    def _validar_notas(self, items: list[dict]) -> None:
        claves = [(item["nota_id"], item["tipo"]) for item in items]
        if len(set(claves)) != len(claves):
            raise ConflictError("El perfil no puede repetir la misma nota y tipo.")

        nota_ids = [item["nota_id"] for item in items]
        notas = {nota.id: nota for nota in self.repository.get_notas_by_ids(nota_ids)}
        faltantes = sorted(set(nota_ids) - set(notas))
        if faltantes:
            raise NotFoundError("Nota no encontrada.")
        if any(not nota.activo for nota in notas.values()):
            raise ConflictError("No se puede usar una nota inactiva.")

    def _to_response(self, producto: ProductoORM) -> PerfilOlfativoResponse:
        acordes = [
            ProductoAcordeResponse(
                id=rel.acorde.id,
                nombre=rel.acorde.nombre,
                slug=rel.acorde.slug,
                intensidad=rel.intensidad,
                posicion=rel.posicion,
            )
            for rel in sorted(
                producto.acordes_rel,
                key=lambda rel: (
                    rel.posicion is None,
                    rel.posicion if rel.posicion is not None else 0,
                    rel.acorde.nombre,
                ),
            )
        ]

        notas_por_tipo = {tipo: [] for tipo in TipoNota}
        for rel in sorted(
            producto.notas_rel,
            key=lambda rel: (
                rel.tipo.value,
                rel.posicion is None,
                rel.posicion if rel.posicion is not None else 0,
                rel.nota.nombre,
            ),
        ):
            notas_por_tipo[rel.tipo].append(
                ProductoNotaResponse(
                    id=rel.nota.id,
                    nombre=rel.nota.nombre,
                    slug=rel.nota.slug,
                    imagen_url=rel.nota.imagen_url,
                    posicion=rel.posicion,
                )
            )

        return PerfilOlfativoResponse(
            producto_id=producto.id,
            acordes=acordes,
            notas=ProductoNotasAgrupadas(
                salida=notas_por_tipo[TipoNota.SALIDA],
                corazon=notas_por_tipo[TipoNota.CORAZON],
                fondo=notas_por_tipo[TipoNota.FONDO],
            ),
        )
