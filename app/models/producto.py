from dataclasses import dataclass
from typing import Optional


@dataclass
class Producto:
    id: Optional[int] = None
    sku: str = ""
    nombre: str = ""
    categoria_id: Optional[int] = None
    marca: str = ""
    descripcion: str = ""
    costo: float = 0.0
    precio: float = 0.0
    stock_actual: int = 0
    stock_minimo: int = 0
    activo: bool = True

    @classmethod
    def desde_fila(cls, fila):
        return cls(
            id=fila["id"],
            sku=fila["sku"],
            nombre=fila["nombre"],
            categoria_id=fila["categoria_id"],
            marca=fila["marca"] or "",
            descripcion=fila["descripcion"] or "",
            costo=float(fila["costo"]),
            precio=float(fila["precio"]),
            stock_actual=int(fila["stock_actual"]),
            stock_minimo=int(fila["stock_minimo"]),
            activo=bool(fila["activo"]),
        )

    def validar(self):
        if not self.sku.strip():
            raise ValueError("El SKU del producto es obligatorio.")
        if not self.nombre.strip():
            raise ValueError("El nombre del producto es obligatorio.")
        if self.costo < 0:
            raise ValueError("El costo no puede ser negativo.")
        if self.precio < 0:
            raise ValueError("El precio no puede ser negativo.")
        if self.stock_actual < 0:
            raise ValueError("El stock actual no puede ser negativo.")
        if self.stock_minimo < 0:
            raise ValueError("El stock minimo no puede ser negativo.")
