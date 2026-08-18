import httpx
import pytest

from app.api_client import ApiClient, ApiConnectionError, UserSession
from app.desktop_config import get_desktop_config, validate_desktop_api_url


def test_development_desktop_allows_local_http():
    assert (
        validate_desktop_api_url("http://127.0.0.1:8000", mode="development")
        == "http://127.0.0.1:8000"
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://api.example.com",
        "https://localhost",
        "https://127.0.0.1:8000",
    ],
)
def test_production_desktop_requires_https_non_localhost(url):
    with pytest.raises(ValueError):
        validate_desktop_api_url(url, mode="production")


def test_production_desktop_accepts_https_url():
    assert (
        validate_desktop_api_url("https://api.example.com", mode="production")
        == "https://api.example.com"
    )


def test_desktop_config_reads_non_secret_env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PERFUMLAB_DESKTOP_MODE", "production")
    monkeypatch.setenv("PERFUMLAB_API_URL", "https://api.example.com")
    monkeypatch.setenv("PERFUMLAB_API_TIMEOUT_SECONDS", "7")

    config = get_desktop_config()

    assert config.mode == "production"
    assert config.api_url == "https://api.example.com"
    assert config.timeout_seconds == 7


def test_api_client_uses_desktop_config_without_backend_settings(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PERFUMLAB_DESKTOP_MODE", "production")
    monkeypatch.setenv("PERFUMLAB_API_URL", "https://api.example.com")

    client = ApiClient(
        session=UserSession(),
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, json={})),
    )
    try:
        assert client.base_url == "https://api.example.com"
    finally:
        client.close()


def test_api_client_rejects_invalid_production_desktop_url(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PERFUMLAB_DESKTOP_MODE", "production")
    monkeypatch.setenv("PERFUMLAB_API_URL", "http://127.0.0.1:8000")

    with pytest.raises(ApiConnectionError):
        ApiClient(session=UserSession())
