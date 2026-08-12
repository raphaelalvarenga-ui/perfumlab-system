from datetime import datetime
from math import ceil

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.tipos import TipoMovimientoInventario
from app.validaciones import validar_texto_requerido


def _validar_motivo(value: str) -> str:
    return validar_texto_requerido(value, "motivo", minimo=1, maximo=160)


class InventarioBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    producto_id: int = Field(..., ge=1, examples=[1])
    motivo: str = Field(..., examples=["Compra de mercaderia"])

    @field_validator("motivo")
    @classmethod
    def validar_motivo(cls, value: str) -> str:
        return _validar_motivo(value)


class InventarioEntrada(InventarioBase):
    cantidad: int = Field(..., gt=0, examples=[10])


class InventarioSalida(InventarioBase):
    cantidad: int = Field(..., gt=0, examples=[2])


class InventarioAjuste(BaseModel):
    model_config = ConfigDict(extra="forbid")

    producto_id: int = Field(..., ge=1, examples=[1])
    stock_nuevo: int = Field(..., ge=0, examples=[15])
    motivo: str = Field(..., examples=["Conteo fisico"])

    @field_validator("motivo")
    @classmethod
    def validar_motivo(cls, value: str) -> str:
        return _validar_motivo(value)


class MovimientoInventarioResponse(BaseModel):
    id: int
    producto_id: int
    tipo: TipoMovimientoInventario
    cantidad: int
    stock_anterior: int
    stock_nuevo: int
    motivo: str
    usuario_id: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MovimientoInventarioListResponse(BaseModel):
    items: list[MovimientoInventarioResponse]
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
