from datetime import datetime
from math import ceil

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.slug import generar_slug
from app.validaciones import validar_texto_opcional, validar_texto_requerido


def normalizar_nombre_nota(value: str) -> str:
    return validar_texto_requerido(
        value,
        "nombre de la nota",
        minimo=2,
        maximo=100,
        requiere_letra=True,
    )


def normalizar_imagen_url(value: str | None) -> str | None:
    if value is None:
        return None
    texto = validar_texto_opcional(value, "imagen_url", maximo=500)
    return texto or None


class NotaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(..., examples=["Toronja"])
    slug: str | None = Field(default=None, examples=["toronja"])
    imagen_url: str | None = None
    activo: bool = True

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str) -> str:
        return normalizar_nombre_nota(value)

    @field_validator("slug")
    @classmethod
    def validar_slug(cls, value: str | None) -> str | None:
        if value is None or str(value).strip() == "":
            return None
        slug = generar_slug(value)
        if not slug:
            raise ValueError("El slug debe contener texto valido.")
        return slug

    @field_validator("imagen_url")
    @classmethod
    def validar_imagen_url(cls, value: str | None) -> str | None:
        return normalizar_imagen_url(value)


class NotaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    slug: str | None = None
    imagen_url: str | None = None
    activo: bool | None = None

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalizar_nombre_nota(value)

    @field_validator("slug")
    @classmethod
    def validar_slug(cls, value: str | None) -> str | None:
        if value is None or str(value).strip() == "":
            return None
        slug = generar_slug(value)
        if not slug:
            raise ValueError("El slug debe contener texto valido.")
        return slug

    @field_validator("imagen_url")
    @classmethod
    def validar_imagen_url(cls, value: str | None) -> str | None:
        return normalizar_imagen_url(value)


class NotaResponse(BaseModel):
    id: int
    nombre: str
    slug: str
    imagen_url: str | None = None
    activo: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class NotaListResponse(BaseModel):
    items: list[NotaResponse]
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
