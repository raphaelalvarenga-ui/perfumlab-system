from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


CONFIG_FILENAME = "perfumlab_desktop.json"
DEFAULT_API_URL = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_DESKTOP_MODE = "development"
DEFAULT_DESKTOP_VERSION = "1.0.0"
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


@dataclass(frozen=True)
class DesktopConfig:
    api_url: str = DEFAULT_API_URL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    mode: str = DEFAULT_DESKTOP_MODE
    app_name: str = "Perfum Lab"
    version: str = DEFAULT_DESKTOP_VERSION

    @property
    def is_production(self) -> bool:
        return self.mode == "production"


def get_desktop_config() -> DesktopConfig:
    file_config = _load_desktop_config_file()
    mode = _first_text(
        os.getenv("PERFUMLAB_DESKTOP_MODE"),
        file_config.get("mode"),
        DEFAULT_DESKTOP_MODE,
    ).lower()
    if mode not in {"development", "production"}:
        raise ValueError("PERFUMLAB_DESKTOP_MODE debe ser development o production.")
    api_url = _first_text(
        os.getenv("PERFUMLAB_API_URL"),
        file_config.get("api_url"),
        DEFAULT_API_URL,
    )
    timeout = _first_float(
        os.getenv("PERFUMLAB_API_TIMEOUT_SECONDS"),
        file_config.get("timeout_seconds"),
        DEFAULT_TIMEOUT_SECONDS,
    )
    if timeout <= 0:
        raise ValueError("PERFUMLAB_API_TIMEOUT_SECONDS debe ser mayor que cero.")
    app_name = _first_text(file_config.get("app_name"), "Perfum Lab")
    version = _first_text(file_config.get("version"), DEFAULT_DESKTOP_VERSION)
    return DesktopConfig(
        api_url=validate_desktop_api_url(api_url, mode=mode),
        timeout_seconds=timeout,
        mode=mode,
        app_name=app_name,
        version=version,
    )


def validate_desktop_api_url(value: str, *, mode: str) -> str:
    api_url = str(value or "").strip().rstrip("/")
    if not api_url:
        raise ValueError("PERFUMLAB_API_URL no esta configurada.")

    parsed = urlparse(api_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("PERFUMLAB_API_URL debe comenzar con http:// o https://.")

    if mode == "production":
        hostname = (parsed.hostname or "").lower()
        if parsed.scheme != "https":
            raise ValueError("PERFUMLAB_API_URL debe usar https:// en produccion.")
        if hostname in LOOPBACK_HOSTS:
            raise ValueError("PERFUMLAB_API_URL de produccion no puede apuntar a localhost.")

    return api_url


def _load_desktop_config_file() -> dict:
    for path in _desktop_config_paths():
        if not path.exists() or not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}
    return {}


def _desktop_config_paths() -> list[Path]:
    paths = []
    if getattr(sys, "frozen", False):
        paths.append(Path(sys.executable).resolve().with_name(CONFIG_FILENAME))
    paths.append(Path.cwd() / CONFIG_FILENAME)
    paths.append(Path(__file__).resolve().parents[1] / CONFIG_FILENAME)
    return paths


def _first_text(*values) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _first_float(*values) -> float:
    for value in values:
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return DEFAULT_TIMEOUT_SECONDS
