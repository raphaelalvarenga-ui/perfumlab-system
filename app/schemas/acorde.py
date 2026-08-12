from datetime import datetime
from math import ceil

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.slug import generar_slug
from app.validaciones import validar_texto_requerido


def normalizar_nombre_acorde(value: str) -> str:
    return validar_texto_requerido(
        value,
        "nombre del acorde",
        minimo=2,
        maximo=80,
        requiere_letra=True,
    )


class AcordeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(..., examples=["Fresco especiado"])
    slug: str | None = Field(default=None, examples=["fresco-especiado"])
    activo: bool = True

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str) -> str:
        return normalizar_nombre_acorde(value)

    @field_validator("slug")
    @classmethod
    def validar_slug(cls, value: str | None) -> str | None:
        if value is None or str(value).strip() == "":
            return None
        slug = generar_slug(value)
        if not slug:
            raise ValueError("El slug debe contener texto valido.")
        return slug


class AcordeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    slug: str | None = None
    activo: bool | None = None

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalizar_nombre_acorde(value)

    @field_validator("slug")
    @classmethod
    def validar_slug(cls, value: str | None) -> str | None:
        if value is None or str(value).strip() == "":
            return None
        slug = generar_slug(value)
        if not slug:
            raise ValueError("El slug debe contener texto valido.")
        return slug


class AcordeResponse(BaseModel):
    id: int
    nombre: str
    slug: str
    activo: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AcordeListResponse(BaseModel):
    items: list[AcordeResponse]
    page: int
    limit: int
    total: int
    pages: int

    @classmethod
    def from_items(cls, *, items: list, page: int, limit: int, total: int):
        return cls(
            items=items,
            page=page,
            limit=limit,
            total=total,
            pages=ceil(total / limit) if total else 0,
        )
