from datetime import datetime
from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.orm.detalle_venta import DetalleVentaORM
from app.models.orm.factura import FacturaORM
from app.models.orm.producto import ProductoORM
from app.models.orm.venta import VentaORM
from app.models.tipos import EstadoFactura, EstadoVenta


ZERO_DECIMAL = Decimal("0.00")


class ReportesRepository:
    def __init__(self, db: Session):
        self.db = db

    def contar_ventas(
        self,
        *,
        estado: EstadoVenta,
        desde: datetime | None,
        hasta_exclusivo: datetime | None,
    ) -> int:
        statement = self._filtrar_fechas(
            select(func.count(VentaORM.id)).where(VentaORM.estado == estado),
            VentaORM.created_at,
            desde=desde,
            hasta_exclusivo=hasta_exclusivo,
        )
        return int(self.db.execute(statement).scalar_one() or 0)

    def sumar_ingresos_ventas_completadas(
        self,
        *,
        desde: datetime | None,
        hasta_exclusivo: datetime | None,
    ) -> Decimal:
        statement = self._filtrar_fechas(
            select(func.coalesce(func.sum(VentaORM.total), ZERO_DECIMAL)).where(
                VentaORM.estado == EstadoVenta.COMPLETADA
            ),
            VentaORM.created_at,
            desde=desde,
            hasta_exclusivo=hasta_exclusivo,
        )
        return self._decimal(statement)

    def sumar_unidades_ventas_completadas(
        self,
        *,
        desde: datetime | None,
        hasta_exclusivo: datetime | None,
    ) -> int:
        statement = (
            select(func.coalesce(func.sum(DetalleVentaORM.cantidad), 0))
            .join(VentaORM, VentaORM.id == DetalleVentaORM.venta_id)
            .where(VentaORM.estado == EstadoVenta.COMPLETADA)
        )
        statement = self._filtrar_fechas(
            statement,
            VentaORM.created_at,
            desde=desde,
            hasta_exclusivo=hasta_exclusivo,
        )
        return int(self.db.execute(statement).scalar_one() or 0)

    def contar_facturas(
        self,
        *,
        estado: EstadoFactura,
        desde: datetime | None,
        hasta_exclusivo: datetime | None,
    ) -> int:
        statement = self._filtrar_fechas(
            select(func.count(FacturaORM.id)).where(FacturaORM.estado == estado),
            FacturaORM.created_at,
            desde=desde,
            hasta_exclusivo=hasta_exclusivo,
        )
        return int(self.db.execute(statement).scalar_one() or 0)

    def contar_productos_stock_bajo(self) -> int:
        statement = select(func.count(ProductoORM.id)).where(
            ProductoORM.activo.is_(True),
            ProductoORM.stock_actual <= ProductoORM.stock_minimo,
        )
        return int(self.db.execute(statement).scalar_one() or 0)

    def ventas_por_periodo(
        self,
        *,
        agrupar: str,
        desde: datetime | None,
        hasta_exclusivo: datetime | None,
    ) -> list[dict]:
        periodo_expr = self._periodo_expression(agrupar)
        ventas_con_unidades = (
            self._filtrar_fechas(
                select(
                    VentaORM.id.label("venta_id"),
                    periodo_expr.label("periodo"),
                    VentaORM.total.label("total"),
                    func.coalesce(func.sum(DetalleVentaORM.cantidad), 0).label(
                        "unidades"
                    ),
                )
                .join(DetalleVentaORM, DetalleVentaORM.venta_id == VentaORM.id)
                .where(VentaORM.estado == EstadoVenta.COMPLETADA)
                .group_by(VentaORM.id, periodo_expr, VentaORM.total),
                VentaORM.created_at,
                desde=desde,
                hasta_exclusivo=hasta_exclusivo,
            )
            .subquery()
        )

        statement = (
            select(
                ventas_con_unidades.c.periodo,
                func.count(ventas_con_unidades.c.venta_id).label("ventas"),
                func.coalesce(func.sum(ventas_con_unidades.c.unidades), 0).label(
                    "unidades"
                ),
                func.coalesce(func.sum(ventas_con_unidades.c.total), ZERO_DECIMAL).label(
                    "ingresos"
                ),
            )
            .group_by(ventas_con_unidades.c.periodo)
            .order_by(ventas_con_unidades.c.periodo.asc())
        )

        return [
            {
                "periodo": row.periodo,
                "ventas": int(row.ventas or 0),
                "unidades": int(row.unidades or 0),
                "ingresos": self._normalizar_decimal(row.ingresos),
            }
            for row in self.db.execute(statement)
        ]

    def productos_mas_vendidos(
        self,
        *,
        desde: datetime | None,
        hasta_exclusivo: datetime | None,
        limit: int,
    ) -> list[dict]:
        statement = (
            select(
                DetalleVentaORM.producto_id,
                DetalleVentaORM.producto_sku,
                DetalleVentaORM.producto_nombre,
                func.coalesce(func.sum(DetalleVentaORM.cantidad), 0).label(
                    "unidades_vendidas"
                ),
                func.coalesce(func.sum(DetalleVentaORM.subtotal), ZERO_DECIMAL).label(
                    "ingresos"
                ),
            )
            .join(VentaORM, VentaORM.id == DetalleVentaORM.venta_id)
            .where(VentaORM.estado == EstadoVenta.COMPLETADA)
            .group_by(
                DetalleVentaORM.producto_id,
                DetalleVentaORM.producto_sku,
                DetalleVentaORM.producto_nombre,
            )
        )
        statement = self._filtrar_fechas(
            statement,
            VentaORM.created_at,
            desde=desde,
            hasta_exclusivo=hasta_exclusivo,
        )
        statement = statement.order_by(
            func.sum(DetalleVentaORM.cantidad).desc(),
            func.sum(DetalleVentaORM.subtotal).desc(),
        ).limit(limit)

        return [
            {
                "producto_id": row.producto_id,
                "producto_sku": row.producto_sku,
                "producto_nombre": row.producto_nombre,
                "unidades_vendidas": int(row.unidades_vendidas or 0),
                "ingresos": self._normalizar_decimal(row.ingresos),
            }
            for row in self.db.execute(statement)
        ]

    def stock_bajo(
        self,
        *,
        page: int,
        limit: int,
    ) -> tuple[list[dict], int]:
        faltante = (ProductoORM.stock_minimo - ProductoORM.stock_actual).label(
            "faltante_minimo"
        )
        base_statement = select(
            ProductoORM.id.label("producto_id"),
            ProductoORM.sku,
            ProductoORM.nombre,
            ProductoORM.marca,
            ProductoORM.stock_actual,
            ProductoORM.stock_minimo,
            faltante,
        ).where(
            ProductoORM.activo.is_(True),
            ProductoORM.stock_actual <= ProductoORM.stock_minimo,
        )
        count_statement = select(func.count(ProductoORM.id)).where(
            ProductoORM.activo.is_(True),
            ProductoORM.stock_actual <= ProductoORM.stock_minimo,
        )

        offset = (page - 1) * limit
        rows = self.db.execute(
            base_statement.order_by(faltante.desc(), ProductoORM.nombre.asc())
            .offset(offset)
            .limit(limit)
        )
        total = int(self.db.execute(count_statement).scalar_one() or 0)
        return (
            [
                {
                    "producto_id": row.producto_id,
                    "sku": row.sku,
                    "nombre": row.nombre,
                    "marca": row.marca,
                    "stock_actual": row.stock_actual,
                    "stock_minimo": row.stock_minimo,
                    "faltante_minimo": max(int(row.faltante_minimo or 0), 0),
                }
                for row in rows
            ],
            total,
        )

    def _periodo_expression(self, agrupar: str):
        if self.db.bind and self.db.bind.dialect.name == "sqlite":
            formato = "%Y-%m-%d" if agrupar == "dia" else "%Y-%m"
            return func.strftime(formato, VentaORM.created_at)

        formato = "YYYY-MM-DD" if agrupar == "dia" else "YYYY-MM"
        return func.to_char(VentaORM.created_at, formato)

    def _filtrar_fechas(
        self,
        statement: Select,
        columna,
        *,
        desde: datetime | None,
        hasta_exclusivo: datetime | None,
    ) -> Select:
        if desde is not None:
            statement = statement.where(columna >= desde)
        if hasta_exclusivo is not None:
            statement = statement.where(columna < hasta_exclusivo)
        return statement

    def _decimal(self, statement: Select) -> Decimal:
        return self._normalizar_decimal(self.db.execute(statement).scalar_one())

    def _normalizar_decimal(self, value) -> Decimal:
        if value is None:
            return ZERO_DECIMAL
        if isinstance(value, Decimal):
            return value.quantize(ZERO_DECIMAL)
        return Decimal(str(value)).quantize(ZERO_DECIMAL)
