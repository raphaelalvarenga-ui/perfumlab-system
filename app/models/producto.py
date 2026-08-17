from dataclasses import dataclass
from typing import Optional

from app.validaciones import (
    validar_decimal_no_negativo,
    validar_decimal_positivo,
    validar_entero_no_negativo,
    validar_sku,
    validar_texto_opcional,
    validar_texto_requerido,
)


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
            id=fila.get("id"),
            sku=fila.get("sku", ""),
            nombre=fila.get("nombre", ""),
            categoria_id=fila.get("categoria_id"),
            marca=fila.get("marca") or "",
            descripcion=fila.get("descripcion") or "",
            costo=float(fila.get("costo") or 0),
            precio=float(fila.get("precio") or 0),
            stock_actual=int(fila.get("stock_actual") or 0),
            stock_minimo=int(fila.get("stock_minimo") or 0),
            activo=bool(fila.get("activo", True)),
        )

    def validar(self):
        self.sku = validar_sku(self.sku)
        self.nombre = validar_texto_requerido(
            self.nombre,
            "nombre del producto",
            minimo=2,
            maximo=120,
            requiere_letra=True,
        )
        self.marca = validar_texto_opcional(self.marca, "marca", maximo=80)
        self.descripcion = validar_texto_opcional(
            self.descripcion,
            "descripcion",
            maximo=500,
        )
        self.costo = validar_decimal_no_negativo(self.costo, "El costo")
        self.precio = validar_decimal_positivo(self.precio, "El precio")
        self.stock_actual = validar_entero_no_negativo(
            self.stock_actual,
            "El stock actual",
        )
        self.stock_minimo = validar_entero_no_negativo(
            self.stock_minimo,
            "El stock minimo",
        )
