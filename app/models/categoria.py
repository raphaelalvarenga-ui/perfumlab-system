from dataclasses import dataclass
from typing import Optional


@dataclass
class Categoria:
    id: Optional[int] = None
    nombre: str = ""
    descripcion: str = ""
    activo: bool = True

    @classmethod
    def desde_fila(cls, fila):
        return cls(
            id=fila["id"],
            nombre=fila["nombre"],
            descripcion=fila["descripcion"] or "",
            activo=bool(fila["activo"]),
        )

    def validar(self):
        if not self.nombre.strip():
            raise ValueError("El nombre de la categoria es obligatorio.")
