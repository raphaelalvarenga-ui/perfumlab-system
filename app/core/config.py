from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Perfum Lab API"
    app_version: str = "1.0.0"
    database_url: str | None = None
    secret_key: str = "change_this_secret_key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    perfume_provider: str = "fragella"
    fragella_api_key: str | None = None
    fragella_base_url: str = "https://api.fragella.com/api/v1"
    fragella_timeout_seconds: float = 10.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

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
