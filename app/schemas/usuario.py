from datetime import datetime
from math import ceil
import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import validate_password_policy
from app.models.tipos import RolUsuario
from app.validaciones import validar_texto_requerido


USERNAME_REGEX = re.compile(r"^[a-z0-9_.-]+$")


def normalizar_username(value: str) -> str:
    username = validar_texto_requerido(
        value,
        "username",
        minimo=3,
        maximo=60,
    ).lower()
    if not USERNAME_REGEX.fullmatch(username):
        raise ValueError(
            "El username solo puede contener letras, numeros, punto, guion y guion bajo."
        )
    return username


def normalizar_email(value) -> str | None:
    if value is None:
        return None
    texto = str(value).strip()
    return texto or None


def email_a_string(value: EmailStr | None) -> str | None:
    if value is None:
        return None
    return str(value).strip().lower()


def validar_password(value: str) -> str:
    return validate_password_policy(value)


class UsuarioCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(..., examples=["Juan Perez"])
    username: str = Field(..., examples=["juan"])
    email: EmailStr | None = Field(default=None, examples=["juan@example.com"])
    password: str = Field(..., min_length=8, max_length=128)
    rol: RolUsuario = Field(..., examples=["VENDEDOR"])
    activo: bool = True

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str) -> str:
        return validar_texto_requerido(
            value,
            "nombre del usuario",
            minimo=2,
            maximo=120,
            requiere_letra=True,
        )

    @field_validator("username")
    @classmethod
    def validar_username(cls, value: str) -> str:
        return normalizar_username(value)

    @field_validator("email", mode="before")
    @classmethod
    def convertir_email_vacio(cls, value):
        return normalizar_email(value)

    @field_validator("email")
    @classmethod
    def validar_email(cls, value: EmailStr | None) -> str | None:
        return email_a_string(value)

    @field_validator("password")
    @classmethod
    def validar_password_usuario(cls, value: str) -> str:
        return validar_password(value)


class UsuarioUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    username: str | None = None
    email: EmailStr | None = None
    rol: RolUsuario | None = None
    activo: bool | None = None

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validar_texto_requerido(
            value,
            "nombre del usuario",
            minimo=2,
            maximo=120,
            requiere_letra=True,
        )

    @field_validator("username")
    @classmethod
    def validar_username(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalizar_username(value)

    @field_validator("email", mode="before")
    @classmethod
    def convertir_email_vacio(cls, value):
        return normalizar_email(value)

    @field_validator("email")
    @classmethod
    def validar_email(cls, value: EmailStr | None) -> str | None:
        return email_a_string(value)


class UsuarioResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password_nueva: str = Field(..., min_length=8, max_length=128)

    @field_validator("password_nueva")
    @classmethod
    def validar_password_nueva(cls, value: str) -> str:
        return validar_password(value)


class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    username: str
    email: str | None = None
    rol: RolUsuario
    activo: bool
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UsuarioListResponse(BaseModel):
    items: list[UsuarioResponse]
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
