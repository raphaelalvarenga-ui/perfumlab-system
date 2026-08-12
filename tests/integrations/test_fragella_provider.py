import httpx
import pytest

from app.integrations.fragella_provider import FragellaProvider
from app.integrations.perfume_provider import (
    ProviderAuthenticationError,
    ProviderBadRequestError,
    ProviderInvalidResponseError,
    ProviderNotFoundError,
    ProviderRateLimitError,
    ProviderUnavailableError,
)
from app.models.tipos import IntensidadAcorde, TipoNota


FRAGELLA_PAYLOAD = {
    "_id": "test",
    "Name": "Invictus",
    "Brand": "Rabanne",
    "Year": "2013",
    "Gender": "Men",
    "Longevity": "Long Lasting",
    "Sillage": "Strong",
    "OilType": "Eau de Toilette",
    "Image URL": "https://example.com/invictus.png",
    "Image URL Transparent": "https://example.com/invictus-clear.png",
    "Main Accords": ["citrus", "marine", "aromatic"],
    "Main Accords Percentage": {
        "citrus": "Dominant",
        "marine": "Prominent",
        "aromatic": "Moderate",
    },
    "Notes": {
        "Top": [
            {"name": "Grapefruit", "imageUrl": "https://example.com/grapefruit.png"}
        ],
        "Middle": [{"name": "Bay Leaf", "imageUrl": "https://example.com/bay.png"}],
        "Base": [{"name": "Guaiac Wood", "imageUrl": "https://example.com/wood.png"}],
    },
}


def provider_with_handler(handler, *, retries=0):
    return FragellaProvider(
        api_key="test-key",
        base_url="https://api.fragella.com/api/v1",
        timeout_seconds=3,
        transport=httpx.MockTransport(handler),
        retries=retries,
        backoff_seconds=0,
    )


def test_search_envia_x_api_key_base_url_y_params():
    captured = {}

    def handler(request):
        captured["url"] = str(request.url)
        captured["key"] = request.headers.get("x-api-key")
        return httpx.Response(200, json=[FRAGELLA_PAYLOAD])

    provider = provider_with_handler(handler)
    results = provider.search_fragrances("Invictus", marca="Rabanne", limit=3)

    assert captured["key"] == "test-key"
    assert captured["url"].startswith("https://api.fragella.com/api/v1/fragrances")
    assert "search=Invictus+Rabanne" in captured["url"]
    assert "limit=3" in captured["url"]
    assert "page=1" in captured["url"]
    assert results[0].external_id == "test"


def test_search_soporta_respuesta_paginada():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "data": [FRAGELLA_PAYLOAD],
                "pagination": {"page": 1, "limit": 5, "count": 1},
            },
        )

    provider = provider_with_handler(handler)
    assert provider.search_fragrances("Invictus")[0].nombre == "Invictus"


def test_get_exacto_normaliza_json_fragella():
    def handler(request):
        assert request.url.path.endswith("/fragrances/test")
        return httpx.Response(200, json=FRAGELLA_PAYLOAD)

    fragrance = provider_with_handler(handler).get_fragrance("test")

    assert fragrance.external_id == "test"
    assert fragrance.nombre == "Invictus"
    assert fragrance.marca == "Rabanne"
    assert fragrance.anio == 2013
    assert fragrance.genero == "Hombre"
    assert fragrance.concentracion == "Eau de Toilette"
    assert fragrance.duracion == "Long Lasting"
    assert fragrance.estela == "Strong"
    assert fragrance.imagen_url == "https://example.com/invictus.png"
    assert fragrance.imagen_transparente_url == "https://example.com/invictus-clear.png"
    assert [(item.nombre, item.intensidad, item.posicion) for item in fragrance.acordes] == [
        ("citrus", IntensidadAcorde.DOMINANTE, 1),
        ("marine", IntensidadAcorde.PROMINENTE, 2),
        ("aromatic", IntensidadAcorde.MODERADO, 3),
    ]
    assert fragrance.notas_salida[0].nombre == "Grapefruit"
    assert fragrance.notas_salida[0].tipo == TipoNota.SALIDA
    assert fragrance.notas_corazon[0].nombre == "Bay Leaf"
    assert fragrance.notas_corazon[0].tipo == TipoNota.CORAZON
    assert fragrance.notas_fondo[0].nombre == "Guaiac Wood"
    assert fragrance.notas_fondo[0].tipo == TipoNota.FONDO


def test_mapeo_seguro_year_gender_e_intensidad_desconocidos():
    payload = {
        **FRAGELLA_PAYLOAD,
        "Year": "unknown",
        "Gender": "For Everybody",
        "Main Accords Percentage": {"citrus": "Very Strong"},
    }

    def handler(request):
        return httpx.Response(200, json=payload)

    fragrance = provider_with_handler(handler).get_fragrance("test")

    assert fragrance.anio is None
    assert fragrance.genero == "For Everybody"
    assert fragrance.acordes[0].intensidad is None


def test_similares_y_usage():
    def handler(request):
        if request.url.path.endswith("/fragrances/similar"):
            assert request.url.params["name"] == "Invictus"
            return httpx.Response(200, json={"data": [FRAGELLA_PAYLOAD]})
        if request.url.path.endswith("/usage"):
            return httpx.Response(
                200,
                json={
                    "plan": "starter",
                    "requests_made": 10,
                    "requests_remaining": 90,
                    "billing_period": "2026-08",
                },
            )
        raise AssertionError(str(request.url))

    provider = provider_with_handler(handler)

    assert provider.get_similar("Invictus", limit=2)[0].external_id == "test"
    assert provider.get_usage() == {
        "plan": "starter",
        "requests_made": 10,
        "requests_remaining": 90,
        "billing_period": "2026-08",
    }


@pytest.mark.parametrize(
    ("status_code", "expected_error"),
    [
        (400, ProviderBadRequestError),
        (401, ProviderAuthenticationError),
        (403, ProviderAuthenticationError),
        (404, ProviderNotFoundError),
        (429, ProviderRateLimitError),
        (500, ProviderUnavailableError),
    ],
)
def test_mapeo_errores_http(status_code, expected_error):
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(status_code, json={"error": "hidden"})

    provider = provider_with_handler(handler, retries=2)

    with pytest.raises(expected_error):
        provider.search_fragrances("Invictus")

    expected_calls = 3 if status_code == 500 else 1
    assert calls == expected_calls


def test_timeout_y_connection_error_hacen_retry_limitado():
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ConnectError("boom", request=request)
        return httpx.Response(200, json=[FRAGELLA_PAYLOAD])

    provider = provider_with_handler(handler, retries=2)

    assert provider.search_fragrances("Invictus")[0].external_id == "test"
    assert calls == 2


def test_429_no_se_reintenta():
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(429, json={"error": "rate limited"})

    provider = provider_with_handler(handler, retries=2)

    with pytest.raises(ProviderRateLimitError):
        provider.search_fragrances("Invictus")
    assert calls == 1


def test_json_invalido_y_respuesta_incompleta():
    invalid_json_provider = provider_with_handler(
        lambda request: httpx.Response(200, content=b"{")
    )
    with pytest.raises(ProviderInvalidResponseError):
        invalid_json_provider.search_fragrances("Invictus")

    incomplete_provider = provider_with_handler(lambda request: httpx.Response(200, json=[{}]))
    with pytest.raises(ProviderInvalidResponseError):
        incomplete_provider.search_fragrances("Invictus")
