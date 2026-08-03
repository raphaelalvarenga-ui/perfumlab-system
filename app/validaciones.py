import math
import re
from datetime import datetime
from pathlib import Path


SKU_REGEX = re.compile(r"^[A-Za-z0-9_-]+$")
ENTERO_REGEX = re.compile(r"^[+-]?\d+$")
CONTROL_REGEX = re.compile(r"[\x00-\x1f\x7f]")


def limpiar_texto(valor):
    if valor is None:
        return ""
    return str(valor).strip()


def validar_texto_requerido(
    valor,
    campo,
    minimo=1,
    maximo=120,
    requiere_letra=False,
):
    texto = limpiar_texto(valor)

    if not texto:
        raise ValueError(f"El {campo} es obligatorio.")

    _validar_texto_base(texto, campo, minimo, maximo, requiere_letra)
    return texto


def validar_texto_opcional(valor, campo, maximo=250, requiere_letra=False):
    texto = limpiar_texto(valor)

    if not texto:
        return ""

    _validar_texto_base(texto, campo, 1, maximo, requiere_letra)
    return texto


def validar_sku(valor):
    sku = validar_texto_requerido(
        valor,
        "SKU del producto",
        minimo=3,
        maximo=30,
    )

    if not SKU_REGEX.fullmatch(sku):
        raise ValueError(
            "El SKU solo puede contener letras, numeros, guiones y guion bajo."
        )

    return sku


def validar_nombre_cliente(valor):
    return validar_texto_requerido(
        valor,
        "nombre del cliente",
        minimo=2,
        maximo=120,
        requiere_letra=True,
    )


def validar_decimal_no_negativo(valor, campo):
    try:
        numero = float(valor)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{campo} debe ser un numero valido.") from error

    if not math.isfinite(numero):
        raise ValueError(f"{campo} debe ser un numero finito.")

    if numero < 0:
        raise ValueError(f"{campo} no puede ser negativo.")

    return numero


def validar_entero_no_negativo(valor, campo):
    numero = _convertir_entero(valor, campo)

    if numero < 0:
        raise ValueError(f"{campo} no puede ser negativo.")

    return numero


def validar_entero_positivo(valor, campo):
    numero = _convertir_entero(valor, campo)

    if numero <= 0:
        raise ValueError(f"{campo} debe ser mayor que cero.")

    return numero


def validar_id_positivo(valor, entidad):
    return validar_entero_positivo(valor, f"ID de {entidad}")


def validar_fecha_iso(valor, campo="fecha"):
    fecha = limpiar_texto(valor)

    if not fecha:
        raise ValueError(f"La {campo} es obligatoria.")

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha):
        raise ValueError(f"La {campo} debe tener formato YYYY-MM-DD.")

    try:
        datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError as error:
        raise ValueError(f"La {campo} no es una fecha valida.") from error

    return fecha


def validar_rango_fechas(fecha_inicio=None, fecha_fin=None):
    inicio = (
        validar_fecha_iso(fecha_inicio, "fecha de inicio")
        if limpiar_texto(fecha_inicio)
        else None
    )
    fin = (
        validar_fecha_iso(fecha_fin, "fecha de fin")
        if limpiar_texto(fecha_fin)
        else None
    )

    if inicio and fin and inicio > fin:
        raise ValueError("La fecha de inicio no puede ser mayor que la fecha de fin.")

    return inicio, fin


def validar_ruta_exportacion(ruta_archivo, extension, descripcion):
    texto_ruta = limpiar_texto(ruta_archivo)

    if not texto_ruta:
        raise ValueError(f"La ruta para exportar {descripcion} es obligatoria.")

    ruta = Path(texto_ruta)

    if ruta.exists() and ruta.is_dir():
        raise ValueError(f"La ruta para exportar {descripcion} debe ser un archivo.")

    if ruta.suffix.lower() != extension.lower():
        raise ValueError(
            f"{descripcion} debe guardarse con extension {extension.lower()}."
        )

    if not ruta.parent.exists():
        raise ValueError(
            f"La carpeta destino para exportar {descripcion} no existe."
        )

    return ruta


def _validar_texto_base(texto, campo, minimo, maximo, requiere_letra):
    if len(texto) < minimo:
        raise ValueError(f"El {campo} debe tener al menos {minimo} caracteres.")

    if len(texto) > maximo:
        raise ValueError(f"El {campo} no puede superar {maximo} caracteres.")

    if CONTROL_REGEX.search(texto):
        raise ValueError(f"El {campo} contiene caracteres no permitidos.")

    if requiere_letra and not any(caracter.isalpha() for caracter in texto):
        raise ValueError(f"El {campo} debe contener al menos una letra.")


def _convertir_entero(valor, campo):
    if isinstance(valor, bool):
        raise ValueError(f"{campo} debe ser un numero entero.")

    if isinstance(valor, float) and not valor.is_integer():
        raise ValueError(f"{campo} debe ser un numero entero.")

    if isinstance(valor, str) and not ENTERO_REGEX.fullmatch(valor.strip()):
        raise ValueError(f"{campo} debe ser un numero entero.")

    try:
        return int(valor)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{campo} debe ser un numero entero.") from error
