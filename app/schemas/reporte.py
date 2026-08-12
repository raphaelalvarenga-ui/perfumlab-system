from datetime import date
from decimal import Decimal
from math import ceil

from pydantic import BaseModel, field_serializer


def _serializar_decimal(value: Decimal) -> str:
    return f"{value:.2f}"


class PeriodoReporte(BaseModel):
    desde: date | None = None
    hasta: date | None = None


class ReporteResumenResponse(BaseModel):
    periodo: PeriodoReporte
    ventas_completadas: int
    ventas_anuladas: int
    ingresos_totales: Decimal
    ticket_promedio: Decimal
    unidades_vendidas: int
    facturas_emitidas: int
    facturas_anuladas: int
    productos_stock_bajo: int

    @field_serializer("ingresos_totales", "ticket_promedio", when_used="json")
    def serializar_decimal(self, value: Decimal) -> str:
        return _serializar_decimal(value)


class VentaPeriodoItem(BaseModel):
    periodo: str
    ventas: int
    unidades: int
    ingresos: Decimal

    @field_serializer("ingresos", when_used="json")
    def serializar_decimal(self, value: Decimal) -> str:
        return _serializar_decimal(value)


class ReporteVentasResponse(BaseModel):
    agrupar: str
    items: list[VentaPeriodoItem]


class ProductoMasVendidoItem(BaseModel):
    producto_id: int
    producto_sku: str
    producto_nombre: str
    unidades_vendidas: int
    ingresos: Decimal

    @field_serializer("ingresos", when_used="json")
    def serializar_decimal(self, value: Decimal) -> str:
        return _serializar_decimal(value)


class ProductosMasVendidosResponse(BaseModel):
    items: list[ProductoMasVendidoItem]


class ProductoStockBajoItem(BaseModel):
    producto_id: int
    sku: str
    nombre: str
    marca: str
    stock_actual: int
    stock_minimo: int
    faltante_minimo: int


class StockBajoResponse(BaseModel):
    items: list[ProductoStockBajoItem]
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
