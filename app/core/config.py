from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


INSECURE_SECRET_VALUES = {
    "change_this_secret_key",
    "secret",
    "password",
    "test",
    "placeholder",
}


class Settings(BaseSettings):
    app_name: str = "Perfum Lab API"
    app_version: str = "1.0.0"
    app_env: str = "development"
    database_url: str | None = Field(default=None, repr=False)
    secret_key: str = Field(default="change_this_secret_key", repr=False)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    cors_allow_credentials: bool = True
    enable_docs: bool = True
    log_level: str = "INFO"
    perfume_provider: str = "fragella"
    fragella_api_key: str | None = Field(default=None, repr=False)
    fragella_base_url: str = "https://api.fragella.com/api/v1"
    fragella_timeout_seconds: float = 10.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("app_env")
    @classmethod
    def normalize_app_env(cls, value: str) -> str:
        text = str(value or "").strip().lower()
        return text or "development"

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        text = str(value or "").strip().upper()
        return text or "INFO"

    @model_validator(mode="after")
    def validate_production_settings(self):
        if not self.is_production:
            return self

        if not self.database_url:
            raise ValueError("DATABASE_URL is required when APP_ENV=production.")

        parsed_database = urlparse(self.database_url)
        if parsed_database.scheme not in {
            "postgresql",
            "postgresql+psycopg",
            "postgresql+psycopg2",
        }:
            raise ValueError("DATABASE_URL must use PostgreSQL when APP_ENV=production.")

        secret = self.secret_key.strip()
        secret_lower = secret.lower()
        if (
            not secret
            or len(secret) < 32
            or secret_lower in INSECURE_SECRET_VALUES
            or "change_this_secret_key" in secret_lower
            or "placeholder" in secret_lower
            or "password" in secret_lower
        ):
            raise ValueError(
                "SECRET_KEY must be a strong non-placeholder value when APP_ENV=production."
            )

        if self.cors_allow_credentials and "*" in self.cors_origin_list:
            raise ValueError(
                "CORS_ORIGINS cannot include '*' with credentials in production."
            )

        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
