from dataclasses import dataclass
from typing import Optional

from app.validaciones import (
    validar_correo,
    validar_nombre_cliente,
    validar_telefono,
    validar_texto_opcional,
)


@dataclass
class Cliente:
    id: Optional[int] = None
    nombre: str = ""
    correo: str = ""
    telefono: str = ""
    direccion: str = ""
    activo: bool = True

    @classmethod
    def desde_fila(cls, fila):
        return cls(
            id=fila.get("id"),
            nombre=fila.get("nombre", ""),
            correo=fila.get("correo", "") or "",
            telefono=fila.get("telefono", "") or "",
            direccion=fila.get("direccion", "") or "",
            activo=bool(fila.get("activo", 1)),
        )

    def validar(self):
        self.nombre = validar_nombre_cliente(self.nombre)
        self.correo = validar_correo(self.correo) if self.correo.strip() else ""
        self.telefono = validar_telefono(self.telefono)
        self.direccion = validar_texto_opcional(
            self.direccion,
            "direccion",
            maximo=180,
        )
