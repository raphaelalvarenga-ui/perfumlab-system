from datetime import datetime
from decimal import Decimal
from math import ceil

from pydantic import BaseModel, ConfigDict, field_serializer

from app.models.tipos import EstadoFactura
from app.schemas.venta import DetalleVentaResponse


def _serializar_decimal(value: Decimal) -> str:
    return f"{value:.2f}"


class FacturaResponse(BaseModel):
    id: int
    numero: str
    venta_id: int
    usuario_id: int | None = None
    cliente_nombre: str
    subtotal: Decimal
    total: Decimal
    estado: EstadoFactura
    created_at: datetime
    anulada_at: datetime | None = None
    motivo_anulacion: str | None = None
    anulada_por_usuario_id: int | None = None
    detalles: list[DetalleVentaResponse]

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("subtotal", "total", when_used="json")
    def serializar_decimal(self, value: Decimal) -> str:
        return _serializar_decimal(value)


class FacturaListResponse(BaseModel):
    items: list[FacturaResponse]
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
