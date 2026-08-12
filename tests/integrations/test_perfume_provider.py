from dataclasses import asdict

import pytest

from app.core.slug import generar_slug
from app.integrations.fragella_provider import FragellaProvider
from app.integrations.perfume_provider import (
    ExternalAccord,
    ExternalFragrance,
    ExternalNote,
    ProviderNotConfiguredError,
)
from app.models.tipos import IntensidadAcorde, TipoNota


def test_generar_slug_normaliza_acentos_espacios_y_mayusculas():
    assert generar_slug("C\u00edtrico") == "citrico"
    assert generar_slug("\u00c1mbar") == "ambar"
    assert generar_slug("Floral blanco") == "floral-blanco"
    assert generar_slug("Fresco especiado") == "fresco-especiado"


def test_external_fragrance_usa_dto_normalizado():
    fragancia = ExternalFragrance(
        external_id="fragella-001",
        nombre="Invictus",
        marca="Rabanne",
        anio=2013,
        genero="Hombre",
        concentracion="EDT",
        duracion="Long lasting",
        estela="Strong",
        imagen_url="https://example.test/invictus.png",
        imagen_transparente_url="https://example.test/invictus-transparent.png",
        acordes=[
            ExternalAccord(
                nombre="Citrico",
                intensidad=IntensidadAcorde.DOMINANTE,
                posicion=0,
            )
        ],
        notas_salida=[
            ExternalNote(
                nombre="Toronja",
                tipo=TipoNota.SALIDA,
                imagen_url="https://example.test/toronja.png",
                posicion=0,
            )
        ],
    )

    data = asdict(fragancia)
    assert data["external_id"] == "fragella-001"
    assert data["anio"] == 2013
    assert data["duracion"] == "Long lasting"
    assert data["estela"] == "Strong"
    assert "fragellaPayload" not in data
    assert "sillage" not in data
    assert data["notas_salida"][0]["tipo"] == TipoNota.SALIDA


@pytest.mark.parametrize(
    ("method_name", "args"),
    [
        ("search_fragrances", ("Invictus",)),
        ("get_fragrance", ("fragella-001",)),
        ("get_similar", ("Invictus",)),
    ],
)
def test_fragella_provider_sin_api_key_no_hace_llamadas_reales(method_name, args):
    provider = FragellaProvider(
        api_key="",
        base_url="https://api.fragella.com/api/v1",
    )

    with pytest.raises(ProviderNotConfiguredError):
        getattr(provider, method_name)(*args)
