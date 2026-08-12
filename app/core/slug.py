import re
import unicodedata


SLUG_SEPARATOR_REGEX = re.compile(r"[^a-z0-9]+")


def generar_slug(value: str) -> str:
    texto = str(value or "").strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = SLUG_SEPARATOR_REGEX.sub("-", texto).strip("-")
    return texto
