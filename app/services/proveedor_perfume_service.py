from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.slug import generar_slug
from app.integrations.perfume_provider import (
    ExternalFragrance,
    ExternalNote,
    PerfumeProvider,
    ProviderAuthenticationError,
    ProviderBadRequestError,
    ProviderInvalidResponseError,
    ProviderNotConfiguredError,
    ProviderNotFoundError,
    ProviderRateLimitError,
    ProviderUnavailableError,
)
from app.models.orm.producto import ProductoORM
from app.models.tipos import TipoNota
from app.repositories.perfumeria_repository import PerfumeriaRepository
from app.repositories.productos_repository import ProductoRepository
from app.schemas.proveedor_perfume import (
    ExternalAccordResponse,
    ExternalFragranceResponse,
    ExternalFragranceSummary,
    ExternalNotesGroupedResponse,
    ExternalNoteResponse,
    FragellaUsageResponse,
    ProductoProveedorCandidatosResponse,
    ProductoSimilaresResponse,
    SincronizacionActualizados,
    SincronizarProveedorResponse,
)
from app.services.exceptions import (
    BadGatewayError,
    BadRequestError,
    ConflictError,
    NotFoundError,
    ServiceError,
    ServiceUnavailableError,
    TooManyRequestsError,
)


logger = logging.getLogger(__name__)
PROVIDER_NAME = "fragella"


class ProveedorPerfumeService:
    def __init__(self, db: Session):
        self.db = db
        self.productos_repository = ProductoRepository(db)
        self.perfumeria_repository = PerfumeriaRepository(db)

    def listar_candidatos(
        self,
        producto_id: int,
        *,
        provider: PerfumeProvider,
        limit: int,
    ) -> ProductoProveedorCandidatosResponse:
        producto = self._obtener_producto(producto_id)
        query = self._query_producto(producto)
        candidatos = self._provider_call(
            lambda: provider.search_fragrances(
                producto.nombre,
                marca=producto.marca,
                limit=limit,
            )
        )
        if not candidatos:
            candidatos = self._provider_call(
                lambda: provider.search_fragrances(producto.nombre, limit=limit)
            )
        return ProductoProveedorCandidatosResponse(
            producto_id=producto.id,
            query=query,
            candidatos=[self._to_summary(item) for item in candidatos],
        )

    def obtener_preview(
        self,
        producto_id: int,
        *,
        external_id: str,
        provider: PerfumeProvider,
    ) -> ExternalFragranceResponse:
        self._obtener_producto(producto_id)
        fragancia = self._provider_call(lambda: provider.get_fragrance(external_id))
        return self._to_fragrance_response(fragancia)

    def sincronizar_producto(
        self,
        producto_id: int,
        *,
        external_id: str,
        provider: PerfumeProvider,
        usuario_id: int,
    ) -> SincronizarProveedorResponse:
        producto = self._obtener_producto(producto_id)
        if not producto.activo:
            raise ConflictError(
                "No se puede sincronizar un producto inactivo con el proveedor."
            )

        self.db.rollback()
        fragancia = self._provider_call(lambda: provider.get_fragrance(external_id))

        try:
            producto = self.perfumeria_repository.get_producto_for_update(producto_id)
            if producto is None:
                raise NotFoundError("Producto no encontrado.")
            if not producto.activo:
                raise ConflictError(
                    "No se puede sincronizar un producto inactivo con el proveedor."
                )

            acordes_payload = self._upsert_acordes(fragancia)
            notas_payload = self._upsert_notas(fragancia)
            self.perfumeria_repository.replace_profile(
                producto.id,
                acordes=acordes_payload,
                notas=notas_payload,
            )
            metadatos = self._actualizar_metadatos(producto, fragancia, external_id)
            self.db.commit()
            self.db.refresh(producto)
            logger.info(
                "fragella_sync_ok",
                extra={
                    "producto_id": producto_id,
                    "external_provider": PROVIDER_NAME,
                    "external_id": external_id,
                    "usuario_id": usuario_id,
                    "resultado": "exito",
                },
            )
            return SincronizarProveedorResponse(
                producto_id=producto.id,
                external_provider=PROVIDER_NAME,
                external_id=external_id,
                external_last_sync=producto.external_last_sync,
                actualizados=SincronizacionActualizados(
                    metadatos=metadatos,
                    acordes=len(acordes_payload),
                    notas=len(notas_payload),
                ),
            )
        except IntegrityError as error:
            self.db.rollback()
            self._log_sync_failure(producto_id, external_id, usuario_id)
            raise ConflictError(
                "La fragancia externa ya esta asociada a otro producto."
            ) from error
        except ServiceError:
            self.db.rollback()
            self._log_sync_failure(producto_id, external_id, usuario_id)
            raise
        except (SQLAlchemyError, Exception) as error:
            self.db.rollback()
            self._log_sync_failure(producto_id, external_id, usuario_id)
            raise ServiceUnavailableError(
                "No se pudo sincronizar el producto con el proveedor externo."
            ) from error

    def listar_similares(
        self,
        producto_id: int,
        *,
        provider: PerfumeProvider,
        limit: int,
    ) -> ProductoSimilaresResponse:
        producto = self._obtener_producto(producto_id)
        similares = self._provider_call(
            lambda: provider.get_similar(producto.nombre, limit=limit)
        )
        return ProductoSimilaresResponse(
            producto_id=producto.id,
            similares=[self._to_summary(item) for item in similares],
        )

    def obtener_usage(self, *, provider: PerfumeProvider) -> FragellaUsageResponse:
        usage = self._provider_call(provider.get_usage)
        return FragellaUsageResponse(
            plan=usage.get("plan"),
            requests_made=usage.get("requests_made"),
            requests_remaining=usage.get("requests_remaining"),
            billing_period=usage.get("billing_period"),
        )

    def _obtener_producto(self, producto_id: int) -> ProductoORM:
        producto = self.productos_repository.get_by_id(producto_id)
        if producto is None:
            raise NotFoundError("Producto no encontrado.")
        return producto

    def _query_producto(self, producto: ProductoORM) -> str:
        return " ".join([producto.nombre, producto.marca]).strip()

    def _upsert_acordes(self, fragancia: ExternalFragrance) -> list[dict]:
        payload = []
        seen_slugs = set()
        for acorde_externo in fragancia.acordes:
            slug = generar_slug(acorde_externo.nombre)
            if not slug or slug in seen_slugs:
                continue
            seen_slugs.add(slug)
            acorde = self.perfumeria_repository.upsert_acorde(
                nombre=acorde_externo.nombre.strip(),
                slug=slug,
            )
            payload.append(
                {
                    "acorde_id": acorde.id,
                    "intensidad": acorde_externo.intensidad,
                    "posicion": acorde_externo.posicion,
                }
            )
        return payload

    def _upsert_notas(self, fragancia: ExternalFragrance) -> list[dict]:
        payload = []
        seen_keys = set()
        for nota_externa in self._iter_notas(fragancia):
            slug = generar_slug(nota_externa.nombre)
            key = (slug, nota_externa.tipo)
            if not slug or key in seen_keys:
                continue
            seen_keys.add(key)
            nota = self.perfumeria_repository.upsert_nota(
                nombre=nota_externa.nombre.strip(),
                slug=slug,
                imagen_url=nota_externa.imagen_url,
            )
            payload.append(
                {
                    "nota_id": nota.id,
                    "tipo": nota_externa.tipo,
                    "posicion": nota_externa.posicion,
                }
            )
        return payload

    def _iter_notas(self, fragancia: ExternalFragrance) -> list[ExternalNote]:
        return [
            *fragancia.notas_salida,
            *fragancia.notas_corazon,
            *fragancia.notas_fondo,
        ]

    def _actualizar_metadatos(
        self,
        producto: ProductoORM,
        fragancia: ExternalFragrance,
        external_id: str,
    ) -> bool:
        changed = False
        for campo, value in {
            "genero": fragancia.genero,
            "anio_lanzamiento": fragancia.anio,
            "concentracion": fragancia.concentracion,
            "duracion": fragancia.duracion,
            "estela": fragancia.estela,
            "external_image_url": fragancia.imagen_url,
            "external_transparent_image_url": fragancia.imagen_transparente_url,
        }.items():
            if value is not None and getattr(producto, campo) != value:
                setattr(producto, campo, value)
                changed = True

        producto.external_provider = PROVIDER_NAME
        producto.external_id = external_id
        producto.external_last_sync = datetime.now(timezone.utc)
        self.db.flush()
        return changed or True

    def _provider_call(self, operation):
        try:
            return operation()
        except ProviderNotConfiguredError as error:
            raise ServiceUnavailableError(
                "El proveedor externo de perfumes no esta configurado."
            ) from error
        except ProviderAuthenticationError as error:
            raise ServiceUnavailableError(
                "El proveedor externo de perfumes no esta configurado correctamente."
            ) from error
        except ProviderBadRequestError as error:
            raise BadGatewayError(
                "La peticion enviada al proveedor externo de perfumes no es valida."
            ) from error
        except ProviderNotFoundError as error:
            raise NotFoundError("Fragancia externa no encontrada.") from error
        except ProviderRateLimitError as error:
            raise TooManyRequestsError(
                "La cuota del proveedor externo de perfumes esta agotada o fue limitada."
            ) from error
        except ProviderUnavailableError as error:
            raise ServiceUnavailableError(
                "El proveedor externo de perfumes no esta disponible temporalmente."
            ) from error
        except ProviderInvalidResponseError as error:
            raise BadGatewayError(
                "La respuesta del proveedor externo de perfumes no es valida."
            ) from error

    def _to_summary(self, fragancia: ExternalFragrance) -> ExternalFragranceSummary:
        return ExternalFragranceSummary(
            external_id=fragancia.external_id,
            nombre=fragancia.nombre,
            marca=fragancia.marca,
            anio=fragancia.anio,
            genero=fragancia.genero,
            imagen_url=fragancia.imagen_url,
        )

    def _to_fragrance_response(
        self,
        fragancia: ExternalFragrance,
    ) -> ExternalFragranceResponse:
        return ExternalFragranceResponse(
            external_id=fragancia.external_id,
            nombre=fragancia.nombre,
            marca=fragancia.marca,
            anio=fragancia.anio,
            genero=fragancia.genero,
            concentracion=fragancia.concentracion,
            duracion=fragancia.duracion,
            estela=fragancia.estela,
            imagen_url=fragancia.imagen_url,
            imagen_transparente_url=fragancia.imagen_transparente_url,
            acordes=[
                ExternalAccordResponse(
                    nombre=acorde.nombre,
                    intensidad=acorde.intensidad,
                    posicion=acorde.posicion,
                )
                for acorde in fragancia.acordes
            ],
            notas=ExternalNotesGroupedResponse(
                salida=[
                    self._to_note_response(nota)
                    for nota in fragancia.notas_salida
                ],
                corazon=[
                    self._to_note_response(nota)
                    for nota in fragancia.notas_corazon
                ],
                fondo=[
                    self._to_note_response(nota)
                    for nota in fragancia.notas_fondo
                ],
            ),
        )

    def _to_note_response(self, nota: ExternalNote) -> ExternalNoteResponse:
        return ExternalNoteResponse(
            nombre=nota.nombre,
            tipo=nota.tipo,
            imagen_url=nota.imagen_url,
            posicion=nota.posicion,
        )

    def _log_sync_failure(
        self,
        producto_id: int,
        external_id: str,
        usuario_id: int,
    ) -> None:
        logger.warning(
            "fragella_sync_failed",
            extra={
                "producto_id": producto_id,
                "external_provider": PROVIDER_NAME,
                "external_id": external_id,
                "usuario_id": usuario_id,
                "resultado": "fallo",
            },
        )
