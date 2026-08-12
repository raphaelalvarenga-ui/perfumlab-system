from enum import Enum


class TipoMovimientoInventario(str, Enum):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    AJUSTE = "AJUSTE"


class EstadoVenta(str, Enum):
    COMPLETADA = "COMPLETADA"
    ANULADA = "ANULADA"
