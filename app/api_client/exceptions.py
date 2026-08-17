from __future__ import annotations

from typing import Any


class ApiError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        detail: Any | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail


class ApiConnectionError(ApiError):
    pass


class ApiAuthenticationError(ApiError):
    pass


class ApiPermissionError(ApiError):
    pass


class ApiValidationError(ApiError):
    pass


class ApiNotFoundError(ApiError):
    pass


class ApiConflictError(ApiError):
    pass


class ApiServerError(ApiError):
    pass


def detail_to_message(detail: Any, *, fallback: str) -> str:
    if detail is None:
        return fallback
    if isinstance(detail, str):
        return detail.strip() or fallback
    if isinstance(detail, dict):
        if "detail" in detail:
            return detail_to_message(detail["detail"], fallback=fallback)
        if "message" in detail:
            return detail_to_message(detail["message"], fallback=fallback)
        partes = [
            detail_to_message(value, fallback="")
            for value in detail.values()
            if value is not None
        ]
        texto = ". ".join(parte for parte in partes if parte)
        return texto or fallback
    if isinstance(detail, list):
        mensajes = []
        for item in detail:
            if isinstance(item, dict):
                campo = _loc_to_label(item.get("loc"))
                mensaje = item.get("msg") or item.get("message") or "Dato invalido."
                mensajes.append(f"{campo}: {mensaje}" if campo else str(mensaje))
            else:
                mensajes.append(detail_to_message(item, fallback=""))
        texto = "\n".join(mensaje for mensaje in mensajes if mensaje)
        return texto or fallback
    return str(detail) or fallback


def _loc_to_label(loc: Any) -> str:
    if not isinstance(loc, list | tuple):
        return ""
    partes = [str(parte) for parte in loc if parte not in {"body", "query", "path"}]
    return ".".join(partes)
