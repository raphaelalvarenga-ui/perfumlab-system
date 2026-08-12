from enum import Enum


class TipoMovimientoInventario(str, Enum):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    AJUSTE = "AJUSTE"


class EstadoVenta(str, Enum):
    COMPLETADA = "COMPLETADA"
    ANULADA = "ANULADA"


class EstadoFactura(str, Enum):
    EMITIDA = "EMITIDA"
    ANULADA = "ANULADA"


class RolUsuario(str, Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    VENDEDOR = "VENDEDOR"


class TipoNota(str, Enum):
    SALIDA = "SALIDA"
    CORAZON = "CORAZON"
    FONDO = "FONDO"


class IntensidadAcorde(str, Enum):
    DOMINANTE = "DOMINANTE"
    PROMINENTE = "PROMINENTE"
    MODERADO = "MODERADO"
    SUTIL = "SUTIL"
