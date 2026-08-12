from datetime import datetime
from math import ceil

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.validaciones import (
    validar_nombre_cliente,
    validar_telefono,
    validar_texto_opcional,
)


def _normalizar_espacios(value: str) -> str:
    return " ".join(str(value).strip().split())


def _normalizar_texto_nullable(
    value: str | None,
    campo: str,
    maximo: int,
) -> str | None:
    if value is None:
        return None
    texto = _normalizar_espacios(value)
    texto = validar_texto_opcional(texto, campo, maximo=maximo)
    return texto or None


class ClienteBase(BaseModel):
    nombre: str = Field(..., examples=["Juan Perez"])
    correo: EmailStr | None = Field(default=None, examples=["juan@example.com"])
    telefono: str | None = Field(default=None, examples=["9999-9999"])
    direccion: str | None = Field(default=None, examples=["La Paz"])
    activo: bool = True

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str) -> str:
        return validar_nombre_cliente(_normalizar_espacios(value))

    @field_validator("correo", mode="before")
    @classmethod
    def correo_vacio_a_none(cls, value):
        if value is None:
            return None
        if str(value).strip() == "":
            return None
        return str(value).strip()

    @field_validator("correo")
    @classmethod
    def normalizar_correo(cls, value: EmailStr | None) -> str | None:
        if value is None:
            return None
        return str(value).strip().lower()

    @field_validator("telefono")
    @classmethod
    def validar_telefono_cliente(cls, value: str | None) -> str | None:
        if value is None:
            return None
        telefono = validar_telefono(_normalizar_espacios(value))
        return telefono or None

    @field_validator("direccion")
    @classmethod
    def validar_direccion(cls, value: str | None) -> str | None:
        return _normalizar_texto_nullable(value, "direccion", 180)


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nombre: str | None = None
    correo: EmailStr | None = None
    telefono: str | None = None
    direccion: str | None = None
    activo: bool | None = None

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validar_nombre_cliente(_normalizar_espacios(value))

    @field_validator("correo", mode="before")
    @classmethod
    def correo_vacio_a_none(cls, value):
        if value is None:
            return None
        if str(value).strip() == "":
            return None
        return str(value).strip()

    @field_validator("correo")
    @classmethod
    def normalizar_correo(cls, value: EmailStr | None) -> str | None:
        if value is None:
            return None
        return str(value).strip().lower()

    @field_validator("telefono")
    @classmethod
    def validar_telefono_cliente(cls, value: str | None) -> str | None:
        if value is None:
            return None
        telefono = validar_telefono(_normalizar_espacios(value))
        return telefono or None

    @field_validator("direccion")
    @classmethod
    def validar_direccion(cls, value: str | None) -> str | None:
        return _normalizar_texto_nullable(value, "direccion", 180)


class ClienteResponse(BaseModel):
    id: int
    nombre: str
    correo: str | None = None
    telefono: str | None = None
    direccion: str | None = None
    activo: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ClienteListResponse(BaseModel):
    items: list[ClienteResponse]
    page: int
    limit: int
    total: int
    pages: int

    @classmethod
    def from_items(
        cls,
        *,
        items: list,
        page: int,
        limit: int,
        total: int,
    ):
        return cls(
            items=items,
            page=page,
            limit=limit,
            total=total,
            pages=ceil(total / limit) if total else 0,
        )
