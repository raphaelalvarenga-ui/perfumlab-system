import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main_api import create_app


POSTGRES_URL = "postgresql+psycopg://postgres:password@localhost:5432/perfumlab"
STRONG_SECRET = "f30b6f8d5d9c4f45a5f243f3b7ea52db7bfc9d1cb38f46de9bb0f4a4a2fd9b40"


def test_production_rejects_placeholder_secret_key():
    with pytest.raises(ValidationError) as error:
        Settings(
            _env_file=None,
            app_env="production",
            database_url=POSTGRES_URL,
            secret_key="change_this_secret_key",
            cors_origins="https://app.example.com",
        )

    assert "SECRET_KEY must be a strong non-placeholder value" in str(error.value)


def test_production_rejects_sqlite_database_url():
    with pytest.raises(ValidationError) as error:
        Settings(
            _env_file=None,
            app_env="production",
            database_url="sqlite:///perfumlab.sqlite3",
            secret_key=STRONG_SECRET,
            cors_origins="https://app.example.com",
        )

    assert "DATABASE_URL must use PostgreSQL" in str(error.value)


def test_production_rejects_cors_wildcard_with_credentials():
    with pytest.raises(ValidationError) as error:
        Settings(
            _env_file=None,
            app_env="production",
            database_url=POSTGRES_URL,
            secret_key=STRONG_SECRET,
            cors_origins="*",
            cors_allow_credentials=True,
        )

    assert "CORS_ORIGINS cannot include '*'" in str(error.value)


def test_production_accepts_strong_server_settings():
    settings = Settings(
        _env_file=None,
        app_env="production",
        database_url=POSTGRES_URL,
        secret_key=STRONG_SECRET,
        cors_origins="https://app.example.com",
        fragella_api_key="fragella-secret-value",
    )

    assert settings.is_production is True
    assert "fragella-secret-value" not in repr(settings)
    assert "postgres:password" not in repr(settings)
    assert STRONG_SECRET not in repr(settings)


def test_development_allows_local_defaults():
    settings = Settings(
        _env_file=None,
        app_env="development",
        database_url="sqlite:///dev.sqlite3",
        secret_key="change_this_secret_key",
    )

    assert settings.is_production is False


def test_docs_can_be_disabled_by_settings():
    settings = Settings(
        _env_file=None,
        app_env="production",
        database_url=POSTGRES_URL,
        secret_key=STRONG_SECRET,
        cors_origins="https://app.example.com",
        enable_docs=False,
    )
    app = create_app(settings)

    assert app.docs_url is None
    assert app.redoc_url is None
    assert app.openapi_url is None

    with TestClient(app) as client:
        assert client.get("/docs").status_code == 404
