from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.tipos import IntensidadAcorde, TipoNota


class ExternalAccordResponse(BaseModel):
    nombre: str
    intensidad: IntensidadAcorde | None = None
    posicion: int | None = None


class ExternalNoteResponse(BaseModel):
    nombre: str
    tipo: TipoNota
    imagen_url: str | None = None
    posicion: int | None = None


class ExternalNotesGroupedResponse(BaseModel):
    salida: list[ExternalNoteResponse]
    corazon: list[ExternalNoteResponse]
    fondo: list[ExternalNoteResponse]


class ExternalFragranceSummary(BaseModel):
    external_id: str
    nombre: str
    marca: str | None = None
    anio: int | None = None
    genero: str | None = None
    imagen_url: str | None = None


class ExternalFragranceResponse(ExternalFragranceSummary):
    concentracion: str | None = None
    duracion: str | None = None
    estela: str | None = None
    imagen_transparente_url: str | None = None
    acordes: list[ExternalAccordResponse]
    notas: ExternalNotesGroupedResponse


class ProductoProveedorCandidatosResponse(BaseModel):
    producto_id: int
    query: str
    candidatos: list[ExternalFragranceSummary]


class ProductoSimilaresResponse(BaseModel):
    producto_id: int
    similares: list[ExternalFragranceSummary]


class SincronizarProveedorRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_id: str = Field(..., min_length=1)

    @field_validator("external_id")
    @classmethod
    def validar_external_id(cls, value: str) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError("external_id es obligatorio.")
        return text


class SincronizacionActualizados(BaseModel):
    metadatos: bool
    acordes: int
    notas: int


class SincronizarProveedorResponse(BaseModel):
    producto_id: int
    external_provider: str
    external_id: str
    external_last_sync: datetime
    actualizados: SincronizacionActualizados


class FragellaUsageResponse(BaseModel):
    plan: str | None = None
    requests_made: int | None = None
    requests_remaining: int | None = None
    billing_period: str | dict[str, Any] | None = None


class FragellaStatusResponse(BaseModel):
    provider: str
    configured: bool
