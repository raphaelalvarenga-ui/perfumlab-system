from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.tipos import EstadoFactura, EstadoVenta
from app.repositories.reportes_repository import ReportesRepository
from app.schemas.reporte import (
    PeriodoReporte,
    ProductosMasVendidosResponse,
    ReporteResumenResponse,
    ReporteVentasResponse,
    StockBajoResponse,
)
from app.services.exceptions import BadRequestError


ZERO_DECIMAL = Decimal("0.00")


class ReportesService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = ReportesRepository(db)

    def obtener_resumen(
        self,
        *,
        desde: date | None = None,
        hasta: date | None = None,
    ) -> ReporteResumenResponse:
        inicio, fin_exclusivo = self._normalizar_periodo(desde, hasta)
        ventas_completadas = self.repository.contar_ventas(
            estado=EstadoVenta.COMPLETADA,
            desde=inicio,
            hasta_exclusivo=fin_exclusivo,
        )
        ventas_anuladas = self.repository.contar_ventas(
            estado=EstadoVenta.ANULADA,
            desde=inicio,
            hasta_exclusivo=fin_exclusivo,
        )
        ingresos_totales = self.repository.sumar_ingresos_ventas_completadas(
            desde=inicio,
            hasta_exclusivo=fin_exclusivo,
        )
        unidades_vendidas = self.repository.sumar_unidades_ventas_completadas(
            desde=inicio,
            hasta_exclusivo=fin_exclusivo,
        )
        facturas_emitidas = self.repository.contar_facturas(
            estado=EstadoFactura.EMITIDA,
            desde=inicio,
            hasta_exclusivo=fin_exclusivo,
        )
        facturas_anuladas = self.repository.contar_facturas(
            estado=EstadoFactura.ANULADA,
            desde=inicio,
            hasta_exclusivo=fin_exclusivo,
        )

        return ReporteResumenResponse(
            periodo=PeriodoReporte(desde=desde, hasta=hasta),
            ventas_completadas=ventas_completadas,
            ventas_anuladas=ventas_anuladas,
            ingresos_totales=ingresos_totales,
            ticket_promedio=self._ticket_promedio(
                ingresos_totales,
                ventas_completadas,
            ),
            unidades_vendidas=unidades_vendidas,
            facturas_emitidas=facturas_emitidas,
            facturas_anuladas=facturas_anuladas,
            productos_stock_bajo=self.repository.contar_productos_stock_bajo(),
        )

    def ventas_por_periodo(
        self,
        *,
        agrupar: str,
        desde: date | None = None,
        hasta: date | None = None,
    ) -> ReporteVentasResponse:
        if agrupar not in {"dia", "mes"}:
            raise BadRequestError("El parametro agrupar debe ser dia o mes.")

        inicio, fin_exclusivo = self._normalizar_periodo(desde, hasta)
        return ReporteVentasResponse(
            agrupar=agrupar,
            items=self.repository.ventas_por_periodo(
                agrupar=agrupar,
                desde=inicio,
                hasta_exclusivo=fin_exclusivo,
            ),
        )

    def productos_mas_vendidos(
        self,
        *,
        limit: int,
        desde: date | None = None,
        hasta: date | None = None,
    ) -> ProductosMasVendidosResponse:
        inicio, fin_exclusivo = self._normalizar_periodo(desde, hasta)
        return ProductosMasVendidosResponse(
            items=self.repository.productos_mas_vendidos(
                desde=inicio,
                hasta_exclusivo=fin_exclusivo,
                limit=limit,
            )
        )

    def stock_bajo(self, *, page: int, limit: int) -> StockBajoResponse:
        items, total = self.repository.stock_bajo(page=page, limit=limit)
        return StockBajoResponse.from_items(
            items=items,
            page=page,
            limit=limit,
            total=total,
        )

    def _normalizar_periodo(
        self,
        desde: date | None,
        hasta: date | None,
    ) -> tuple[datetime | None, datetime | None]:
        if desde is not None and hasta is not None and desde > hasta:
            raise BadRequestError("La fecha desde no puede ser mayor que hasta.")

        inicio = (
            datetime.combine(desde, time.min, tzinfo=timezone.utc)
            if desde is not None
            else None
        )
        fin_exclusivo = (
            datetime.combine(hasta + timedelta(days=1), time.min, tzinfo=timezone.utc)
            if hasta is not None
            else None
        )
        return inicio, fin_exclusivo

    def _ticket_promedio(
        self,
        ingresos_totales: Decimal,
        ventas_completadas: int,
    ) -> Decimal:
        if ventas_completadas <= 0:
            return ZERO_DECIMAL
        return (ingresos_totales / ventas_completadas).quantize(ZERO_DECIMAL)
