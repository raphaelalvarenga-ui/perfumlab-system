from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.models.tipos import IntensidadAcorde, TipoNota


class ProviderNotConfiguredError(RuntimeError):
    pass


@dataclass(slots=True)
class ExternalAccord:
    nombre: str
    intensidad: IntensidadAcorde | None = None
    posicion: int | None = None


@dataclass(slots=True)
class ExternalNote:
    nombre: str
    tipo: TipoNota
    imagen_url: str | None = None
    posicion: int | None = None


@dataclass(slots=True)
class ExternalFragrance:
    external_id: str
    nombre: str
    marca: str | None = None
    anio: int | None = None
    genero: str | None = None
    concentracion: str | None = None
    duracion: str | None = None
    estela: str | None = None
    imagen_url: str | None = None
    imagen_transparente_url: str | None = None
    acordes: list[ExternalAccord] = field(default_factory=list)
    notas_salida: list[ExternalNote] = field(default_factory=list)
    notas_corazon: list[ExternalNote] = field(default_factory=list)
    notas_fondo: list[ExternalNote] = field(default_factory=list)


class PerfumeProvider(Protocol):
    def search_fragrances(
        self,
        nombre: str,
        marca: str | None = None,
    ) -> list[ExternalFragrance]:
        ...

    def get_fragrance(self, external_id: str) -> ExternalFragrance:
        ...

    def get_similar(self, nombre: str, limit: int = 10) -> list[ExternalFragrance]:
        ...
