from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.validaciones import validar_texto_requerido


class CategoriaCreate(BaseModel):
    nombre: str = Field(..., examples=["Hombre"])
    activo: bool = True

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str) -> str:
        return validar_texto_requerido(
            value,
            "nombre de la categoria",
            minimo=2,
            maximo=80,
            requiere_letra=True,
        )


class CategoriaUpdate(BaseModel):
    nombre: str | None = Field(default=None, examples=["Fragancias masculinas"])
    activo: bool | None = None

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validar_texto_requerido(
            value,
            "nombre de la categoria",
            minimo=2,
            maximo=80,
            requiere_letra=True,
        )


class CategoriaResponse(BaseModel):
    id: int
    nombre: str
    activo: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
