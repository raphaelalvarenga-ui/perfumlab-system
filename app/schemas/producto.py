from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.validaciones import (
    validar_sku,
    validar_texto_opcional,
    validar_texto_requerido,
)


def _validar_decimal_no_negativo(value: Decimal | None, campo: str) -> Decimal | None:
    if value is None:
        return None
    if not value.is_finite():
        raise ValueError(f"{campo} debe ser un numero finito.")
    if value < 0:
        raise ValueError(f"{campo} no puede ser negativo.")
    return value


def _validar_entero_no_negativo(value: int | None, campo: str) -> int | None:
    if value is None:
        return None
    if value < 0:
        raise ValueError(f"{campo} no puede ser negativo.")
    return value


def _validar_texto_nullable(
    value: str | None,
    campo: str,
    maximo: int,
) -> str | None:
    if value is None:
        return None
    texto = validar_texto_opcional(value, campo, maximo=maximo)
    return texto or None


class ProductoBase(BaseModel):
    sku: str = Field(..., examples=["PERF-001"])
    nombre: str = Field(..., examples=["Invictus"])
    marca: str = Field(..., examples=["Rabanne"])
    descripcion: str | None = Field(default=None, examples=["Fragancia masculina"])
    categoria_id: int = Field(..., ge=1, examples=[1])
    costo: Decimal = Field(default=Decimal("0.00"), ge=0, examples=["150.00"])
    precio: Decimal = Field(default=Decimal("0.00"), ge=0, examples=["280.00"])
    stock_minimo: int = Field(default=0, ge=0)
    ml: int | None = Field(default=None, gt=0, examples=[50])
    imagen: str | None = None
    activo: bool = True
    genero: str | None = Field(default=None, examples=["Hombre"])
    anio_lanzamiento: int | None = Field(default=None, ge=0, examples=[2013])
    concentracion: str | None = None
    duracion: str | None = None
    estela: str | None = None
    external_provider: str | None = None
    external_id: str | None = None
    external_last_sync: datetime | None = None

    @field_validator("sku")
    @classmethod
    def validar_sku_producto(cls, value: str) -> str:
        return validar_sku(value)

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str) -> str:
        return validar_texto_requerido(
            value,
            "nombre del producto",
            minimo=2,
            maximo=120,
            requiere_letra=True,
        )

    @field_validator("marca")
    @classmethod
    def validar_marca(cls, value: str) -> str:
        return validar_texto_requerido(
            value,
            "marca",
            minimo=2,
            maximo=80,
            requiere_letra=True,
        )

    @field_validator("descripcion")
    @classmethod
    def validar_descripcion(cls, value: str | None) -> str | None:
        return _validar_texto_nullable(value, "descripcion", 500)

    @field_validator("costo")
    @classmethod
    def validar_costo(cls, value: Decimal) -> Decimal:
        return _validar_decimal_no_negativo(value, "El costo")

    @field_validator("precio")
    @classmethod
    def validar_precio(cls, value: Decimal) -> Decimal:
        return _validar_decimal_no_negativo(value, "El precio")

    @field_validator("stock_minimo")
    @classmethod
    def validar_stock_minimo(cls, value: int) -> int:
        return _validar_entero_no_negativo(value, "El stock minimo")

    @field_validator("genero")
    @classmethod
    def validar_genero(cls, value: str | None) -> str | None:
        return _validar_texto_nullable(value, "genero", 40)

    @field_validator("concentracion")
    @classmethod
    def validar_concentracion(cls, value: str | None) -> str | None:
        return _validar_texto_nullable(value, "concentracion", 60)

    @field_validator("duracion")
    @classmethod
    def validar_duracion(cls, value: str | None) -> str | None:
        return _validar_texto_nullable(value, "duracion", 60)

    @field_validator("estela")
    @classmethod
    def validar_estela(cls, value: str | None) -> str | None:
        return _validar_texto_nullable(value, "estela", 60)

    @field_validator("external_provider")
    @classmethod
    def validar_external_provider(cls, value: str | None) -> str | None:
        return _validar_texto_nullable(value, "external_provider", 80)

    @field_validator("external_id")
    @classmethod
    def validar_external_id(cls, value: str | None) -> str | None:
        return _validar_texto_nullable(value, "external_id", 120)


class ProductoCreate(ProductoBase):
    stock_actual: int = Field(default=0, ge=0)

    @field_validator("stock_actual")
    @classmethod
    def validar_stock_actual(cls, value: int) -> int:
        return _validar_entero_no_negativo(value, "El stock actual")


class ProductoReplace(ProductoBase):
    model_config = ConfigDict(extra="forbid")


class ProductoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str | None = None
    nombre: str | None = None
    marca: str | None = None
    descripcion: str | None = None
    categoria_id: int | None = Field(default=None, ge=1)
    costo: Decimal | None = Field(default=None, ge=0)
    precio: Decimal | None = Field(default=None, ge=0)
    stock_minimo: int | None = Field(default=None, ge=0)
    ml: int | None = Field(default=None, gt=0)
    imagen: str | None = None
    activo: bool | None = None
    genero: str | None = None
    anio_lanzamiento: int | None = Field(default=None, ge=0)
    concentracion: str | None = None
    duracion: str | None = None
    estela: str | None = None
    external_provider: str | None = None
    external_id: str | None = None
    external_last_sync: datetime | None = None

    @field_validator("sku")
    @classmethod
    def validar_sku_producto(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validar_sku(value)

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validar_texto_requerido(
            value,
            "nombre del producto",
            minimo=2,
            maximo=120,
            requiere_letra=True,
        )

    @field_validator("marca")
    @classmethod
    def validar_marca(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validar_texto_requerido(
            value,
            "marca",
            minimo=2,
            maximo=80,
            requiere_letra=True,
        )

    @field_validator("descripcion")
    @classmethod
    def validar_descripcion(cls, value: str | None) -> str | None:
        return _validar_texto_nullable(value, "descripcion", 500)

    @field_validator("costo")
    @classmethod
    def validar_costo(cls, value: Decimal | None) -> Decimal | None:
        return _validar_decimal_no_negativo(value, "El costo")

    @field_validator("precio")
    @classmethod
    def validar_precio(cls, value: Decimal | None) -> Decimal | None:
        return _validar_decimal_no_negativo(value, "El precio")

    @field_validator("stock_minimo")
    @classmethod
    def validar_stock_minimo(cls, value: int | None) -> int | None:
        return _validar_entero_no_negativo(value, "El stock minimo")

    @field_validator("genero")
    @classmethod
    def validar_genero(cls, value: str | None) -> str | None:
        return _validar_texto_nullable(value, "genero", 40)

    @field_validator("concentracion")
    @classmethod
    def validar_concentracion(cls, value: str | None) -> str | None:
        return _validar_texto_nullable(value, "concentracion", 60)

    @field_validator("duracion")
    @classmethod
    def validar_duracion(cls, value: str | None) -> str | None:
        return _validar_texto_nullable(value, "duracion", 60)

    @field_validator("estela")
    @classmethod
    def validar_estela(cls, value: str | None) -> str | None:
        return _validar_texto_nullable(value, "estela", 60)

    @field_validator("external_provider")
    @classmethod
    def validar_external_provider(cls, value: str | None) -> str | None:
        return _validar_texto_nullable(value, "external_provider", 80)

    @field_validator("external_id")
    @classmethod
    def validar_external_id(cls, value: str | None) -> str | None:
        return _validar_texto_nullable(value, "external_id", 120)


class ProductoResponse(ProductoBase):
    id: int
    stock_actual: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("costo", "precio", when_used="json")
    def serializar_decimal(self, value: Decimal) -> str:
        return f"{value:.2f}"


class ProductoListResponse(BaseModel):
    items: list[ProductoResponse]
    page: int
    limit: int
    total: int
    pages: int
