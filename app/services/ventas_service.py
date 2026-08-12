from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.orm.cliente import ClienteORM
from app.models.orm.producto import ProductoORM
from app.models.orm.venta import utc_now
from app.models.tipos import EstadoFactura, EstadoVenta
from app.repositories.clientes_repository import ClienteRepository
from app.repositories.facturas_repository import FacturasRepository
from app.repositories.ventas_repository import VentasRepository
from app.schemas.venta import VentaListResponse
from app.services.exceptions import BadRequestError, ConflictError, NotFoundError
from app.services.stock_service import StockService


CLIENTE_MOSTRADOR = "Cliente mostrador"


class VentasService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = VentasRepository(db)
        self.clientes_repository = ClienteRepository(db)
        self.facturas_repository = FacturasRepository(db)
        self.stock_service = StockService(db)

    def registrar_venta(self, datos: dict, *, usuario_id: int):
        try:
            cantidades = self._agrupar_productos(datos["productos"])
            cliente = self._obtener_cliente_para_venta(datos.get("cliente_id"))
            productos = self._bloquear_y_validar_productos(cantidades)
            detalle_plan = self._preparar_detalles(cantidades, productos)
            total = sum(item["subtotal"] for item in detalle_plan)

            venta = self.repository.create(
                {
                    "cliente_id": cliente.id if cliente else None,
                    "cliente_nombre": cliente.nombre if cliente else CLIENTE_MOSTRADOR,
                    "usuario_id": usuario_id,
                    "estado": EstadoVenta.COMPLETADA,
                    "subtotal": total,
                    "total": total,
                }
            )

            for item in detalle_plan:
                producto = item["producto"]
                self.repository.create_detalle(
                    {
                        "venta_id": venta.id,
                        "producto_id": producto.id,
                        "producto_sku": producto.sku,
                        "producto_nombre": producto.nombre,
                        "precio_unitario": item["precio_unitario"],
                        "cantidad": item["cantidad"],
                        "subtotal": item["subtotal"],
                    }
                )
                self.stock_service.registrar_salida_en_producto(
                    producto,
                    cantidad=item["cantidad"],
                    motivo=f"Venta #{venta.id}",
                    usuario_id=usuario_id,
                    mensaje_stock_insuficiente=(
                        f"No hay suficiente stock para el producto {producto.nombre}."
                    ),
                )

            venta_id = venta.id
            self.db.commit()
            venta_guardada = self.repository.get_by_id(venta_id)
            return venta_guardada
        except Exception:
            self.db.rollback()
            raise

    def listar_ventas(
        self,
        *,
        page: int,
        limit: int,
        cliente_id: int | None = None,
        estado: EstadoVenta | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> VentaListResponse:
        items, total = self.repository.list(
            page=page,
            limit=limit,
            cliente_id=cliente_id,
            estado=estado,
            desde=desde,
            hasta=hasta,
        )
        return VentaListResponse.from_items(
            items=items,
            page=page,
            limit=limit,
            total=total,
        )

    def obtener_venta(self, venta_id: int):
        venta = self.repository.get_by_id(venta_id)
        if venta is None:
            raise NotFoundError("Venta no encontrada.")
        return venta

    def anular_venta(self, venta_id: int, datos: dict, *, usuario_id: int):
        motivo = datos["motivo"].strip()
        try:
            venta = self.repository.get_by_id_for_update(venta_id)
            if venta is None:
                raise NotFoundError("Venta no encontrada.")
            if venta.estado == EstadoVenta.ANULADA:
                raise ConflictError("La venta ya esta anulada.")

            detalles = list(venta.detalles)
            productos = self._bloquear_productos_para_anulacion(detalles)
            for detalle in detalles:
                producto = productos.get(detalle.producto_id)
                self.stock_service.registrar_entrada_en_producto(
                    producto,
                    cantidad=detalle.cantidad,
                    motivo=f"Anulacion de venta #{venta.id}: {motivo}",
                    usuario_id=usuario_id,
                    requiere_activo=False,
                )

            venta.estado = EstadoVenta.ANULADA
            venta.anulada_at = utc_now()
            venta.motivo_anulacion = motivo
            venta.anulada_por_usuario_id = usuario_id
            self.db.flush()

            factura = self.facturas_repository.get_by_venta_id(venta.id)
            if factura is not None and factura.estado == EstadoFactura.EMITIDA:
                self.facturas_repository.mark_anulada(
                    factura,
                    motivo=motivo,
                    anulada_at=venta.anulada_at,
                    anulada_por_usuario_id=usuario_id,
                )

            venta_id = venta.id
            self.db.commit()
            return self.repository.get_by_id(venta_id)
        except Exception:
            self.db.rollback()
            raise

    def _obtener_cliente_para_venta(self, cliente_id: int | None) -> ClienteORM | None:
        if cliente_id is None:
            return None

        cliente = self.clientes_repository.get_by_id(cliente_id)
        if cliente is None:
            raise NotFoundError("Cliente no encontrado.")
        if not cliente.activo:
            raise ConflictError("El cliente esta inactivo.")
        return cliente

    def _agrupar_productos(self, items: list[dict]) -> dict[int, int]:
        cantidades: dict[int, int] = {}
        for item in items:
            producto_id = item["producto_id"]
            cantidad = item["cantidad"]
            cantidades[producto_id] = cantidades.get(producto_id, 0) + cantidad

        if not cantidades:
            raise BadRequestError("Debe agregar al menos un producto a la venta.")
        return cantidades

    def _bloquear_y_validar_productos(
        self,
        cantidades: dict[int, int],
    ) -> dict[int, ProductoORM]:
        productos_bloqueados = self.stock_service.bloquear_productos_ordenados(
            list(cantidades)
        )
        productos = {producto.id: producto for producto in productos_bloqueados}
        for producto_id in sorted(cantidades):
            producto = productos.get(producto_id)
            if producto is None:
                raise NotFoundError("Producto no encontrado.")
            self.stock_service.validar_producto_operable(producto)
            cantidad = cantidades[producto_id]
            if cantidad > int(producto.stock_actual):
                raise BadRequestError(
                    f"No hay suficiente stock para el producto {producto.nombre}."
                )
        return productos

    def _preparar_detalles(
        self,
        cantidades: dict[int, int],
        productos: dict[int, ProductoORM],
    ) -> list[dict]:
        detalles = []
        for producto_id in sorted(cantidades):
            producto = productos[producto_id]
            cantidad = cantidades[producto_id]
            precio_unitario = Decimal(producto.precio).quantize(Decimal("0.01"))
            subtotal = (precio_unitario * cantidad).quantize(Decimal("0.01"))
            detalles.append(
                {
                    "producto": producto,
                    "cantidad": cantidad,
                    "precio_unitario": precio_unitario,
                    "subtotal": subtotal,
                }
            )
        return detalles

    def _bloquear_productos_para_anulacion(self, detalles: list) -> dict[int, ProductoORM]:
        producto_ids = sorted({detalle.producto_id for detalle in detalles})
        productos_bloqueados = self.stock_service.bloquear_productos_ordenados(
            producto_ids
        )
        productos = {producto.id: producto for producto in productos_bloqueados}
        for producto_id in producto_ids:
            if producto_id not in productos:
                raise NotFoundError("Producto no encontrado.")
        return productos
