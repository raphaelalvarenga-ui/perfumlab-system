from pydantic import BaseModel, ConfigDict, Field

from app.models.tipos import IntensidadAcorde, TipoNota


class ProductoAcordeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acorde_id: int = Field(..., ge=1)
    intensidad: IntensidadAcorde | None = None
    posicion: int | None = Field(default=None, ge=0)


class ProductoNotaInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nota_id: int = Field(..., ge=1)
    tipo: TipoNota
    posicion: int | None = Field(default=None, ge=0)


class PerfilOlfativoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acordes: list[ProductoAcordeInput] = Field(default_factory=list)
    notas: list[ProductoNotaInput] = Field(default_factory=list)


class ProductoAcordeResponse(BaseModel):
    id: int
    nombre: str
    slug: str
    intensidad: IntensidadAcorde | None = None
    posicion: int | None = None


class ProductoNotaResponse(BaseModel):
    id: int
    nombre: str
    slug: str
    imagen_url: str | None = None
    posicion: int | None = None


class ProductoNotasAgrupadas(BaseModel):
    salida: list[ProductoNotaResponse]
    corazon: list[ProductoNotaResponse]
    fondo: list[ProductoNotaResponse]


class PerfilOlfativoResponse(BaseModel):
    producto_id: int
    acordes: list[ProductoAcordeResponse]
    notas: ProductoNotasAgrupadas
