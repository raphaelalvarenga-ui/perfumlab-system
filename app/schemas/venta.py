from datetime import datetime
from decimal import Decimal
from math import ceil

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.models.tipos import EstadoVenta
from app.validaciones import validar_texto_requerido


def _serializar_decimal(value: Decimal) -> str:
    return f"{value:.2f}"


class VentaItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    producto_id: int = Field(..., ge=1, examples=[10])
    cantidad: int = Field(..., gt=0, examples=[2])


class VentaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cliente_id: int | None = Field(default=None, ge=1, examples=[1])
    productos: list[VentaItemCreate] = Field(..., min_length=1)


class VentaAnularRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    motivo: str = Field(..., examples=["Cliente cancelo la compra"])

    @field_validator("motivo")
    @classmethod
    def validar_motivo(cls, value: str) -> str:
        return validar_texto_requerido(value, "motivo", minimo=1, maximo=180)


class DetalleVentaResponse(BaseModel):
    id: int
    venta_id: int
    producto_id: int
    producto_sku: str
    producto_nombre: str
    precio_unitario: Decimal
    cantidad: int
    subtotal: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("precio_unitario", "subtotal", when_used="json")
    def serializar_decimal(self, value: Decimal) -> str:
        return _serializar_decimal(value)


class VentaResponse(BaseModel):
    id: int
    cliente_id: int | None = None
    cliente_nombre: str
    usuario_id: int | None = None
    estado: EstadoVenta
    subtotal: Decimal
    total: Decimal
    detalles: list[DetalleVentaResponse]
    created_at: datetime
    anulada_at: datetime | None = None
    motivo_anulacion: str | None = None
    anulada_por_usuario_id: int | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("subtotal", "total", when_used="json")
    def serializar_decimal(self, value: Decimal) -> str:
        return _serializar_decimal(value)


class VentaListResponse(BaseModel):
    items: list[VentaResponse]
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
