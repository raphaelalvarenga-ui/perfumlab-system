from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.tipos import EstadoFactura, EstadoVenta
from app.repositories.facturas_repository import FacturasRepository
from app.repositories.ventas_repository import VentasRepository
from app.schemas.factura import FacturaListResponse
from app.services.exceptions import ConflictError, NotFoundError


class FacturasService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = FacturasRepository(db)
        self.ventas_repository = VentasRepository(db)

    def generar_factura(self, venta_id: int, *, usuario_id: int):
        try:
            venta = self.ventas_repository.get_by_id_for_update(venta_id)
            if venta is None:
                raise NotFoundError("Venta no encontrada.")
            if venta.estado == EstadoVenta.ANULADA:
                raise ConflictError("No se puede facturar una venta anulada.")
            if self.repository.get_by_venta_id(venta_id) is not None:
                raise ConflictError("La venta ya tiene una factura.")

            factura = self.repository.create(
                {
                    "numero": self._numero_factura(venta.id),
                    "venta_id": venta.id,
                    "cliente_nombre": venta.cliente_nombre,
                    "subtotal": venta.subtotal,
                    "total": venta.total,
                    "estado": EstadoFactura.EMITIDA,
                    "usuario_id": usuario_id,
                }
            )
            factura_id = factura.id
            self.db.commit()
            return self.repository.get_by_id(factura_id)
        except IntegrityError as error:
            self.db.rollback()
            raise ConflictError("La venta ya tiene una factura.") from error
        except Exception:
            self.db.rollback()
            raise

    def obtener_factura(self, factura_id: int):
        factura = self.repository.get_by_id(factura_id)
        if factura is None:
            raise NotFoundError("Factura no encontrada.")
        return factura

    def obtener_por_numero(self, numero: str):
        factura = self.repository.get_by_numero(numero)
        if factura is None:
            raise NotFoundError("Factura no encontrada.")
        return factura

    def listar_facturas(
        self,
        *,
        page: int,
        limit: int,
        venta_id: int | None = None,
        estado: EstadoFactura | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        buscar: str | None = None,
    ) -> FacturaListResponse:
        items, total = self.repository.list(
            page=page,
            limit=limit,
            venta_id=venta_id,
            estado=estado,
            desde=desde,
            hasta=hasta,
            buscar=buscar,
        )
        return FacturaListResponse.from_items(
            items=items,
            page=page,
            limit=limit,
            total=total,
        )

    def _numero_factura(self, venta_id: int) -> str:
        return f"FAC-{venta_id:06d}"
