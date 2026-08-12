from datetime import datetime, timezone

from app.integrations.factory import get_perfume_provider
from app.integrations.perfume_provider import (
    ExternalAccord,
    ExternalFragrance,
    ExternalNote,
    ProviderNotConfiguredError,
    ProviderRateLimitError,
    ProviderUnavailableError,
)
from app.models.tipos import IntensidadAcorde, TipoNota


def crear_categoria(client, nombre="Fragella"):
    response = client.post("/api/v1/categorias", json={"nombre": nombre})
    assert response.status_code == 201
    return response.json()


def crear_producto(client, categoria_id, **overrides):
    data = {
        "sku": "FRAG-001",
        "nombre": "Invictus Local",
        "marca": "Marca Local",
        "descripcion": "Producto local para Fragella",
        "categoria_id": categoria_id,
        "costo": "150.00",
        "precio": "280.00",
        "stock_actual": 10,
        "stock_minimo": 2,
        "ml": 50,
        "genero": None,
    }
    data.update(overrides)
    response = client.post("/api/v1/productos", json=data)
    assert response.status_code == 201
    return response.json()


def fragancia(
    external_id="ext-a",
    nombre="Invictus",
    marca="Rabanne",
    anio=2013,
    genero="Hombre",
    concentracion="Eau de Toilette",
    duracion="Long Lasting",
    estela="Strong",
    acordes=None,
    salida=None,
    corazon=None,
    fondo=None,
):
    return ExternalFragrance(
        external_id=external_id,
        nombre=nombre,
        marca=marca,
        anio=anio,
        genero=genero,
        concentracion=concentracion,
        duracion=duracion,
        estela=estela,
        imagen_url="https://example.test/image.png",
        imagen_transparente_url="https://example.test/transparent.png",
        acordes=acordes
        if acordes is not None
        else [
            ExternalAccord("Citrico", IntensidadAcorde.DOMINANTE, 1),
            ExternalAccord("Marino", IntensidadAcorde.PROMINENTE, 2),
        ],
        notas_salida=salida
        if salida is not None
        else [ExternalNote("Grapefruit", TipoNota.SALIDA, "https://example.test/g.png", 1)],
        notas_corazon=corazon
        if corazon is not None
        else [ExternalNote("Bay Leaf", TipoNota.CORAZON, "https://example.test/b.png", 1)],
        notas_fondo=fondo
        if fondo is not None
        else [ExternalNote("Guaiac Wood", TipoNota.FONDO, "https://example.test/w.png", 1)],
    )


class FakeProvider:
    def __init__(
        self,
        *,
        search_results=None,
        fallback_results=None,
        fragrance=None,
        similar_results=None,
        usage=None,
        error=None,
    ):
        self.search_results = search_results if search_results is not None else []
        self.fallback_results = fallback_results if fallback_results is not None else []
        self.fragrance = fragrance or fragancia()
        self.similar_results = similar_results if similar_results is not None else []
        self.usage = usage or {
            "plan": "starter",
            "requests_made": 10,
            "requests_remaining": 90,
            "billing_period": "2026-08",
        }
        self.error = error
        self.search_calls = []
        self.get_calls = []
        self.similar_calls = []

    def search_fragrances(self, query, marca=None, limit=5):
        self.search_calls.append((query, marca, limit))
        if self.error:
            raise self.error
        if len(self.search_calls) == 1:
            return self.search_results
        return self.fallback_results

    def get_fragrance(self, external_id):
        self.get_calls.append(external_id)
        if self.error:
            raise self.error
        return self.fragrance

    def get_similar(self, nombre, limit=5):
        self.similar_calls.append((nombre, limit))
        if self.error:
            raise self.error
        return self.similar_results

    def get_usage(self):
        if self.error:
            raise self.error
        return self.usage


def override_provider(app, provider):
    app.dependency_overrides[get_perfume_provider] = lambda: provider


def clear_provider(app):
    app.dependency_overrides.pop(get_perfume_provider, None)


def test_candidatos_busca_nombre_marca_y_no_persiste(client):
    categoria = crear_categoria(client)
    producto = crear_producto(client, categoria["id"])
    provider = FakeProvider(search_results=[fragancia()])
    override_provider(client.app, provider)
    try:
        response = client.get(
            f"/api/v1/productos/{producto['id']}/proveedor/candidatos",
            params={"limit": 3},
        )
    finally:
        clear_provider(client.app)

    assert response.status_code == 200
    data = response.json()
    assert data["producto_id"] == producto["id"]
    assert data["query"] == "Invictus Local Marca Local"
    assert data["candidatos"][0]["external_id"] == "ext-a"
    assert provider.search_calls == [("Invictus Local", "Marca Local", 3)]

    response = client.get(f"/api/v1/productos/{producto['id']}")
    producto_actual = response.json()
    assert producto_actual["external_id"] is None
    assert producto_actual["external_provider"] is None

    response = client.get(f"/api/v1/productos/{producto['id']}/perfil-olfativo")
    assert response.json()["acordes"] == []


def test_candidatos_hace_un_fallback_por_nombre_si_no_hay_resultados(client):
    categoria = crear_categoria(client)
    producto = crear_producto(client, categoria["id"])
    provider = FakeProvider(search_results=[], fallback_results=[fragancia()])
    override_provider(client.app, provider)
    try:
        response = client.get(f"/api/v1/productos/{producto['id']}/proveedor/candidatos")
    finally:
        clear_provider(client.app)

    assert response.status_code == 200
    assert len(response.json()["candidatos"]) == 1
    assert provider.search_calls == [
        ("Invictus Local", "Marca Local", 5),
        ("Invictus Local", None, 5),
    ]


def test_preview_no_persiste(client):
    categoria = crear_categoria(client)
    producto = crear_producto(client, categoria["id"])
    provider = FakeProvider(fragrance=fragancia())
    override_provider(client.app, provider)
    try:
        response = client.get(
            f"/api/v1/productos/{producto['id']}/proveedor/candidatos/ext-a"
        )
    finally:
        clear_provider(client.app)

    assert response.status_code == 200
    data = response.json()
    assert data["external_id"] == "ext-a"
    assert data["notas"]["salida"][0]["nombre"] == "Grapefruit"
    assert provider.get_calls == ["ext-a"]

    response = client.get(f"/api/v1/productos/{producto['id']}")
    assert response.json()["external_id"] is None


def test_sync_enriquece_sin_modificar_datos_de_negocio(client):
    categoria = crear_categoria(client)
    producto = crear_producto(client, categoria["id"])
    provider = FakeProvider(fragrance=fragancia())
    override_provider(client.app, provider)
    try:
        response = client.post(
            f"/api/v1/productos/{producto['id']}/sincronizar-proveedor",
            json={"external_id": "ext-a"},
        )
    finally:
        clear_provider(client.app)

    assert response.status_code == 200
    data = response.json()
    assert data["external_provider"] == "fragella"
    assert data["external_id"] == "ext-a"
    assert data["external_last_sync"] is not None
    assert data["actualizados"] == {"metadatos": True, "acordes": 2, "notas": 3}

    response = client.get(f"/api/v1/productos/{producto['id']}")
    producto_actual = response.json()
    assert producto_actual["sku"] == "FRAG-001"
    assert producto_actual["nombre"] == "Invictus Local"
    assert producto_actual["marca"] == "Marca Local"
    assert producto_actual["precio"] == "280.00"
    assert producto_actual["stock_actual"] == 10
    assert producto_actual["stock_minimo"] == 2
    assert producto_actual["genero"] == "Hombre"
    assert producto_actual["anio_lanzamiento"] == 2013
    assert producto_actual["concentracion"] == "Eau de Toilette"
    assert producto_actual["duracion"] == "Long Lasting"
    assert producto_actual["estela"] == "Strong"
    assert producto_actual["external_image_url"] == "https://example.test/image.png"
    assert producto_actual["imagen"] is None

    response = client.get(f"/api/v1/productos/{producto['id']}/perfil-olfativo")
    perfil = response.json()
    assert [item["slug"] for item in perfil["acordes"]] == ["citrico", "marino"]
    assert [item["slug"] for item in perfil["notas"]["salida"]] == ["grapefruit"]
    assert [item["slug"] for item in perfil["notas"]["corazon"]] == ["bay-leaf"]
    assert [item["slug"] for item in perfil["notas"]["fondo"]] == ["guaiac-wood"]


def test_sync_no_sobrescribe_metadatos_con_none_ni_imagen_manual_nota(client):
    categoria = crear_categoria(client)
    producto = crear_producto(
        client,
        categoria["id"],
        genero="Unisex",
        anio_lanzamiento=1999,
        concentracion="EDP",
    )
    nota = client.post(
        "/api/v1/notas",
        json={"nombre": "Grapefruit", "imagen_url": "https://manual.test/g.png"},
    ).json()
    provider = FakeProvider(
        fragrance=fragancia(
            anio=None,
            genero=None,
            concentracion=None,
            salida=[
                ExternalNote(
                    "Grapefruit",
                    TipoNota.SALIDA,
                    "https://provider.test/g.png",
                    1,
                )
            ],
        )
    )
    override_provider(client.app, provider)
    try:
        response = client.post(
            f"/api/v1/productos/{producto['id']}/sincronizar-proveedor",
            json={"external_id": "ext-a"},
        )
    finally:
        clear_provider(client.app)

    assert response.status_code == 200
    response = client.get(f"/api/v1/productos/{producto['id']}")
    producto_actual = response.json()
    assert producto_actual["genero"] == "Unisex"
    assert producto_actual["anio_lanzamiento"] == 1999
    assert producto_actual["concentracion"] == "EDP"

    response = client.get(f"/api/v1/notas/{nota['id']}")
    assert response.json()["imagen_url"] == "https://manual.test/g.png"


def test_sync_reactiva_acordes_y_notas_inactivas(client):
    categoria = crear_categoria(client)
    producto = crear_producto(client, categoria["id"])
    acorde = client.post("/api/v1/acordes", json={"nombre": "Citrico"}).json()
    nota = client.post("/api/v1/notas", json={"nombre": "Grapefruit"}).json()
    assert client.delete(f"/api/v1/acordes/{acorde['id']}").status_code == 200
    assert client.delete(f"/api/v1/notas/{nota['id']}").status_code == 200

    provider = FakeProvider(fragrance=fragancia(acordes=[ExternalAccord("Citrico")]))
    override_provider(client.app, provider)
    try:
        response = client.post(
            f"/api/v1/productos/{producto['id']}/sincronizar-proveedor",
            json={"external_id": "ext-a"},
        )
    finally:
        clear_provider(client.app)

    assert response.status_code == 200
    assert client.get(f"/api/v1/acordes/{acorde['id']}").json()["activo"] is True
    assert client.get(f"/api/v1/notas/{nota['id']}").json()["activo"] is True


def test_resync_no_duplica_y_actualiza_last_sync(client):
    categoria = crear_categoria(client)
    producto = crear_producto(client, categoria["id"])
    provider = FakeProvider(fragrance=fragancia())
    override_provider(client.app, provider)
    try:
        first = client.post(
            f"/api/v1/productos/{producto['id']}/sincronizar-proveedor",
            json={"external_id": "ext-a"},
        )
        second = client.post(
            f"/api/v1/productos/{producto['id']}/sincronizar-proveedor",
            json={"external_id": "ext-a"},
        )
    finally:
        clear_provider(client.app)

    assert first.status_code == 200
    assert second.status_code == 200
    assert datetime.fromisoformat(second.json()["external_last_sync"]) >= datetime.fromisoformat(
        first.json()["external_last_sync"]
    )
    response = client.get(f"/api/v1/productos/{producto['id']}/perfil-olfativo")
    perfil = response.json()
    assert len(perfil["acordes"]) == 2
    assert len(perfil["notas"]["salida"]) == 1


def test_reasignacion_reemplaza_perfil_completo(client):
    categoria = crear_categoria(client)
    producto = crear_producto(client, categoria["id"])
    provider_a = FakeProvider(fragrance=fragancia(external_id="ext-a"))
    override_provider(client.app, provider_a)
    try:
        assert client.post(
            f"/api/v1/productos/{producto['id']}/sincronizar-proveedor",
            json={"external_id": "ext-a"},
        ).status_code == 200
    finally:
        clear_provider(client.app)

    provider_b = FakeProvider(
        fragrance=fragancia(
            external_id="ext-b",
            acordes=[ExternalAccord("Dulce", IntensidadAcorde.SUTIL, 1)],
            salida=[],
            corazon=[],
            fondo=[ExternalNote("Vainilla", TipoNota.FONDO, None, 1)],
        )
    )
    override_provider(client.app, provider_b)
    try:
        response = client.post(
            f"/api/v1/productos/{producto['id']}/sincronizar-proveedor",
            json={"external_id": "ext-b"},
        )
    finally:
        clear_provider(client.app)

    assert response.status_code == 200
    assert response.json()["external_id"] == "ext-b"
    perfil = client.get(f"/api/v1/productos/{producto['id']}/perfil-olfativo").json()
    assert [item["slug"] for item in perfil["acordes"]] == ["dulce"]
    assert perfil["notas"]["salida"] == []
    assert [item["slug"] for item in perfil["notas"]["fondo"]] == ["vainilla"]


def test_atomicidad_sync_rollback_si_falla_db(client, monkeypatch):
    categoria = crear_categoria(client)
    producto = crear_producto(client, categoria["id"])

    def fail_replace_profile(*args, **kwargs):
        raise RuntimeError("fallo forzado")

    monkeypatch.setattr(
        "app.repositories.perfumeria_repository.PerfumeriaRepository.replace_profile",
        fail_replace_profile,
    )
    provider = FakeProvider(fragrance=fragancia())
    override_provider(client.app, provider)
    try:
        response = client.post(
            f"/api/v1/productos/{producto['id']}/sincronizar-proveedor",
            json={"external_id": "ext-a"},
        )
    finally:
        clear_provider(client.app)

    assert response.status_code == 503
    producto_actual = client.get(f"/api/v1/productos/{producto['id']}").json()
    assert producto_actual["external_id"] is None
    perfil = client.get(f"/api/v1/productos/{producto['id']}/perfil-olfativo").json()
    assert perfil["acordes"] == []


def test_similares_usage_status_y_permisos(client, public_client, vendedor_headers):
    categoria = crear_categoria(client)
    producto = crear_producto(client, categoria["id"])
    provider = FakeProvider(similar_results=[fragancia(external_id="similar-1")])
    override_provider(client.app, provider)
    try:
        assert public_client.get(
            f"/api/v1/productos/{producto['id']}/similares"
        ).status_code == 401
        response = client.get(
            f"/api/v1/productos/{producto['id']}/similares",
            headers=vendedor_headers,
            params={"limit": 3},
        )
        assert response.status_code == 200
        assert response.json()["similares"][0]["external_id"] == "similar-1"

        assert client.get(
            f"/api/v1/productos/{producto['id']}/proveedor/candidatos",
            headers=vendedor_headers,
        ).status_code == 403
        assert client.get(
            f"/api/v1/productos/{producto['id']}/proveedor/candidatos/ext-a",
            headers=vendedor_headers,
        ).status_code == 403
        assert client.post(
            f"/api/v1/productos/{producto['id']}/sincronizar-proveedor",
            headers=vendedor_headers,
            json={"external_id": "ext-a"},
        ).status_code == 403
        assert client.get(
            "/api/v1/integraciones/fragella/usage",
            headers=vendedor_headers,
        ).status_code == 403
        assert client.get(
            "/api/v1/integraciones/fragella/status",
            headers=vendedor_headers,
        ).status_code == 403

        response = client.get("/api/v1/integraciones/fragella/usage")
        assert response.status_code == 200
        assert response.json()["requests_remaining"] == 90
    finally:
        clear_provider(client.app)


def test_provider_no_configurado_y_rate_limit_devuelven_mensajes_limpios(client):
    categoria = crear_categoria(client)
    producto = crear_producto(client, categoria["id"])

    provider = FakeProvider(error=ProviderNotConfiguredError())
    override_provider(client.app, provider)
    try:
        response = client.get(f"/api/v1/productos/{producto['id']}/similares")
    finally:
        clear_provider(client.app)
    assert response.status_code == 503
    assert response.json()["detail"] == "El proveedor externo de perfumes no esta configurado."

    provider = FakeProvider(error=ProviderRateLimitError())
    override_provider(client.app, provider)
    try:
        response = client.get(f"/api/v1/productos/{producto['id']}/similares")
    finally:
        clear_provider(client.app)
    assert response.status_code == 429
    assert "cuota" in response.json()["detail"].lower()


def test_provider_no_disponible_devuelve_503(client):
    categoria = crear_categoria(client)
    producto = crear_producto(client, categoria["id"])
    provider = FakeProvider(error=ProviderUnavailableError())
    override_provider(client.app, provider)
    try:
        response = client.get(f"/api/v1/productos/{producto['id']}/similares")
    finally:
        clear_provider(client.app)

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "El proveedor externo de perfumes no esta disponible temporalmente."
    )
