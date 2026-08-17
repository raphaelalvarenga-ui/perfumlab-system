from dataclasses import dataclass
from typing import Optional

from app.validaciones import validar_texto_opcional, validar_texto_requerido


@dataclass
class Categoria:
    id: Optional[int] = None
    nombre: str = ""
    descripcion: str = ""
    activo: bool = True

    @classmethod
    def desde_fila(cls, fila):
        return cls(
            id=fila.get("id"),
            nombre=fila.get("nombre", ""),
            descripcion=fila.get("descripcion") or "",
            activo=bool(fila.get("activo", True)),
        )

    def validar(self):
        self.nombre = validar_texto_requerido(
            self.nombre,
            "nombre de la categoria",
            minimo=2,
            maximo=80,
            requiere_letra=True,
        )
        self.descripcion = validar_texto_opcional(
            self.descripcion,
            "descripcion de la categoria",
            maximo=250,
        )
