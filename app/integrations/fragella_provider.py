from __future__ import annotations

import time
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import get_settings
from app.integrations.perfume_provider import (
    ExternalAccord,
    ExternalFragrance,
    ExternalNote,
    ProviderAuthenticationError,
    ProviderBadRequestError,
    ProviderInvalidResponseError,
    ProviderNotConfiguredError,
    ProviderNotFoundError,
    ProviderRateLimitError,
    ProviderUnavailableError,
)
from app.models.tipos import IntensidadAcorde, TipoNota


TEMPORARY_STATUS_CODES = {500, 502, 503, 504}
MAX_RETRIES = 2


GENDER_MAP = {
    "men": "Hombre",
    "man": "Hombre",
    "male": "Hombre",
    "women": "Mujer",
    "woman": "Mujer",
    "female": "Mujer",
    "unisex": "Unisex",
}


INTENSITY_MAP = {
    "dominant": IntensidadAcorde.DOMINANTE,
    "prominent": IntensidadAcorde.PROMINENTE,
    "moderate": IntensidadAcorde.MODERADO,
    "subtle": IntensidadAcorde.SUTIL,
}


NOTE_TYPE_MAP = {
    "Top": TipoNota.SALIDA,
    "Middle": TipoNota.CORAZON,
    "Base": TipoNota.FONDO,
}


class FragellaProvider:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        client: httpx.Client | None = None,
        transport: httpx.BaseTransport | None = None,
        retries: int = MAX_RETRIES,
        backoff_seconds: float = 0.15,
    ):
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.fragella_api_key
        self.base_url = (base_url or settings.fragella_base_url).rstrip("/")
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.fragella_timeout_seconds
        )
        self._client = client
        self._transport = transport
        self.retries = max(0, min(retries, MAX_RETRIES))
        self.backoff_seconds = max(0.0, backoff_seconds)

    def search_fragrances(
        self,
        query: str,
        marca: str | None = None,
        limit: int = 5,
    ) -> list[ExternalFragrance]:
        search = self._build_search_query(query, marca)
        payload = self._get(
            "/fragrances",
            params={"search": search, "limit": limit, "page": 1},
        )
        items = self._extract_collection(payload)
        return [self._normalize_fragrance(item) for item in items]

    def get_fragrance(self, external_id: str) -> ExternalFragrance:
        external_id = self._normalize_required_text(external_id, "external_id")
        payload = self._get(f"/fragrances/{quote(external_id, safe='')}")
        if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
            payload = payload["data"]
        return self._normalize_fragrance(payload)

    def get_similar(self, nombre: str, limit: int = 5) -> list[ExternalFragrance]:
        nombre = self._normalize_required_text(nombre, "nombre")
        payload = self._get(
            "/fragrances/similar",
            params={"name": nombre, "limit": limit},
        )
        items = self._extract_collection(payload)
        return [self._normalize_fragrance(item) for item in items]

    def get_usage(self) -> dict:
        payload = self._get("/usage")

        if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
            payload = payload["data"]

        if not isinstance(payload, dict):
            raise ProviderInvalidResponseError("Respuesta de uso invalida.")

        usage = payload.get("usage")
        if not isinstance(usage, dict):
            usage = payload

        requests_made = usage.get("requests_made")
        if requests_made is None:
            requests_made = usage.get("requestsMade")
        if requests_made is None:
            requests_made = usage.get("Requests Made")

        requests_remaining = usage.get("requests_remaining")
        if requests_remaining is None:
            requests_remaining = usage.get("requestsRemaining")
        if requests_remaining is None:
            requests_remaining = usage.get("Requests Remaining")

        billing_period = payload.get("billing_period")
        if billing_period is None:
            billing_period = payload.get("billingPeriod")
        if billing_period is None:
            billing_period = payload.get("Billing Period")

        return {
            "plan": payload.get("plan") or payload.get("Plan"),
            "requests_made": requests_made,
            "requests_remaining": requests_remaining,
            "billing_period": billing_period,
        }

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        self._ensure_configured()
        last_error: ProviderUnavailableError | None = None
        for attempt in range(self.retries + 1):
            try:
                response = self._request(path, params=params)
            except (httpx.TimeoutException, httpx.NetworkError) as error:
                last_error = ProviderUnavailableError(
                    "Proveedor externo temporalmente no disponible."
                )
                if attempt < self.retries:
                    self._sleep_before_retry(attempt)
                    continue
                raise last_error from error
            except httpx.RequestError as error:
                raise ProviderUnavailableError(
                    "Proveedor externo temporalmente no disponible."
                ) from error

            if response.status_code in TEMPORARY_STATUS_CODES and attempt < self.retries:
                self._sleep_before_retry(attempt)
                continue
            self._raise_for_status(response)
            try:
                return response.json()
            except ValueError as error:
                raise ProviderInvalidResponseError(
                    "Respuesta JSON invalida del proveedor."
                ) from error

        raise last_error or ProviderUnavailableError(
            "Proveedor externo temporalmente no disponible."
        )

    def _request(
        self,
        path: str,
        *,
        params: dict[str, Any] | None,
    ) -> httpx.Response:
        headers = {"x-api-key": str(self.api_key)}
        if self._client is not None:
            return self._client.get(
                path,
                params=params,
                headers=headers,
                timeout=self.timeout_seconds,
            )
        with httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout_seconds,
            transport=self._transport,
        ) as client:
            return client.get(path, params=params, headers=headers)

    def _raise_for_status(self, response: httpx.Response) -> None:
        status_code = response.status_code
        if 200 <= status_code < 300:
            return
        if status_code == 400:
            raise ProviderBadRequestError("Peticion externa invalida.")
        if status_code in {401, 403}:
            raise ProviderAuthenticationError("Autenticacion del proveedor invalida.")
        if status_code == 404:
            raise ProviderNotFoundError("Fragancia externa no encontrada.")
        if status_code == 429:
            raise ProviderRateLimitError("Cuota del proveedor agotada.")
        if status_code in TEMPORARY_STATUS_CODES:
            raise ProviderUnavailableError(
                "Proveedor externo temporalmente no disponible."
            )
        raise ProviderInvalidResponseError("Respuesta HTTP inesperada del proveedor.")

    def _normalize_fragrance(self, item: Any) -> ExternalFragrance:
        if not isinstance(item, dict):
            raise ProviderInvalidResponseError("Fragancia externa invalida.")

        external_id = self._first_text(item, "_id", "id", "external_id")
        nombre = self._first_text(item, "Name", "name", "nombre")
        if not external_id or not nombre:
            raise ProviderInvalidResponseError("Fragancia externa incompleta.")

        notes = self._normalize_notes(item.get("Notes") or item.get("notes") or {})
        return ExternalFragrance(
            external_id=external_id,
            nombre=nombre,
            marca=self._first_text(item, "Brand", "brand", "marca"),
            anio=self._parse_year(item.get("Year") or item.get("year")),
            genero=self._normalize_gender(item.get("Gender") or item.get("gender")),
            concentracion=self._first_text(item, "OilType", "Oil Type", "oilType"),
            duracion=self._first_text(item, "Longevity", "longevity"),
            estela=self._first_text(item, "Sillage", "sillage"),
            imagen_url=self._first_text(item, "Image URL", "imageUrl", "image_url"),
            imagen_transparente_url=self._first_text(
                item,
                "Image URL Transparent",
                "imageUrlTransparent",
                "image_transparent_url",
            ),
            acordes=self._normalize_accords(item),
            notas_salida=notes[TipoNota.SALIDA],
            notas_corazon=notes[TipoNota.CORAZON],
            notas_fondo=notes[TipoNota.FONDO],
        )

    def _normalize_accords(self, item: dict[str, Any]) -> list[ExternalAccord]:
        raw_accords = item.get("Main Accords") or item.get("mainAccords") or []
        raw_percentages = (
            item.get("Main Accords Percentage")
            or item.get("mainAccordsPercentage")
            or {}
        )
        if not isinstance(raw_accords, list):
            return []
        if not isinstance(raw_percentages, dict):
            raw_percentages = {}

        accords = []
        for index, raw_acord in enumerate(raw_accords, start=1):
            nombre = self._extract_name(raw_acord)
            if not nombre:
                continue
            raw_intensity = None
            if isinstance(raw_acord, dict):
                raw_intensity = (
                    raw_acord.get("intensity")
                    or raw_acord.get("Intensity")
                    or raw_acord.get("percentage")
                )
            if raw_intensity is None:
                raw_intensity = raw_percentages.get(nombre)
            accords.append(
                ExternalAccord(
                    nombre=nombre,
                    intensidad=self._normalize_intensity(raw_intensity),
                    posicion=index,
                )
            )
        return accords

    def _normalize_notes(self, raw_notes: Any) -> dict[TipoNota, list[ExternalNote]]:
        notes = {tipo: [] for tipo in TipoNota}
        if not isinstance(raw_notes, dict):
            return notes

        for external_key, tipo in NOTE_TYPE_MAP.items():
            raw_items = raw_notes.get(external_key) or raw_notes.get(external_key.lower())
            if not isinstance(raw_items, list):
                continue
            for index, raw_note in enumerate(raw_items, start=1):
                nombre = self._extract_name(raw_note)
                if not nombre:
                    continue
                imagen_url = None
                if isinstance(raw_note, dict):
                    imagen_url = self._first_text(
                        raw_note,
                        "imageUrl",
                        "Image URL",
                        "imagen_url",
                    )
                notes[tipo].append(
                    ExternalNote(
                        nombre=nombre,
                        tipo=tipo,
                        imagen_url=imagen_url,
                        posicion=index,
                    )
                )
        return notes

    def _normalize_gender(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        return GENDER_MAP.get(text.lower(), text)

    def _normalize_intensity(self, value: Any) -> IntensidadAcorde | None:
        if value is None:
            return None
        return INTENSITY_MAP.get(str(value).strip().lower())

    def _parse_year(self, value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return None

    def _extract_collection(self, payload: Any) -> list[Any]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            data = payload.get("data")
            if data is None:
                data = payload.get("fragrances") or payload.get("results")
            if data is None:
                return []
            if isinstance(data, list):
                return data
        raise ProviderInvalidResponseError("Coleccion externa invalida.")

    def _build_search_query(self, query: str, marca: str | None) -> str:
        query = self._normalize_required_text(query, "query")
        marca_text = str(marca or "").strip()
        if marca_text:
            return f"{query} {marca_text}"
        return query

    def _normalize_required_text(self, value: Any, field_name: str) -> str:
        text = str(value or "").strip()
        if not text:
            raise ProviderBadRequestError(f"{field_name} es obligatorio.")
        return text

    def _first_text(self, item: dict[str, Any], *keys: str) -> str | None:
        for key in keys:
            value = item.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return None

    def _extract_name(self, value: Any) -> str | None:
        if isinstance(value, str):
            text = value.strip()
            return text or None
        if isinstance(value, dict):
            return self._first_text(value, "name", "Name", "nombre")
        return None

    def _ensure_configured(self) -> None:
        if not self.api_key or not str(self.api_key).strip():
            raise ProviderNotConfiguredError(
                "Fragella no esta configurado. Define FRAGELLA_API_KEY."
            )
        if not self.base_url:
            raise ProviderNotConfiguredError(
                "Fragella no esta configurado. Define FRAGELLA_BASE_URL."
            )

    def _sleep_before_retry(self, attempt: int) -> None:
        if self.backoff_seconds:
            time.sleep(self.backoff_seconds * (attempt + 1))
