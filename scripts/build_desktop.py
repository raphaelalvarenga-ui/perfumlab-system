from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist" / "PerfumLab"
BUILD_DIR = PROJECT_ROOT / "build" / "PerfumLab"

sys.path.insert(0, str(PROJECT_ROOT))

from app.desktop_config import (  # noqa: E402
    CONFIG_FILENAME,
    DEFAULT_API_URL,
    DEFAULT_DESKTOP_VERSION,
    DEFAULT_TIMEOUT_SECONDS,
    validate_desktop_api_url,
)


def main() -> int:
    args = parse_args()
    mode = args.mode.strip().lower()
    api_url = args.api_url or os.getenv("PERFUMLAB_API_URL")
    if not api_url and mode == "development":
        api_url = DEFAULT_API_URL
    if not api_url:
        raise SystemExit(
            "PERFUMLAB_API_URL es obligatorio para construir el desktop en production."
        )

    try:
        api_url = validate_desktop_api_url(api_url, mode=mode)
    except ValueError as error:
        raise SystemExit(str(error)) from None
    timeout = float(args.timeout_seconds)
    if timeout <= 0:
        raise SystemExit("PERFUMLAB_API_TIMEOUT_SECONDS debe ser mayor que cero.")

    if args.clean:
        _remove_controlled(BUILD_DIR)
        _remove_controlled(DIST_DIR)

    env = os.environ.copy()
    env["APP_ENV"] = "development"
    env["PERFUMLAB_DESKTOP_MODE"] = mode
    env["PERFUMLAB_API_URL"] = api_url
    env["PERFUMLAB_API_TIMEOUT_SECONDS"] = str(timeout)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "PerfumLab.spec",
        ],
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
    )

    if not DIST_DIR.exists():
        raise SystemExit(f"No se encontro el directorio generado: {DIST_DIR}")

    config_path = DIST_DIR / CONFIG_FILENAME
    config_path.write_text(
        json.dumps(
            {
                "mode": mode,
                "api_url": api_url,
                "timeout_seconds": timeout,
                "app_name": "Perfum Lab",
                "version": DEFAULT_DESKTOP_VERSION,
            },
            indent=2,
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )

    exe_path = DIST_DIR / "PerfumLab.exe"
    if not exe_path.exists():
        raise SystemExit(f"No se encontro el ejecutable generado: {exe_path}")

    print(f"Build generado: {exe_path}")
    print(f"Config desktop: {config_path}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Construye PerfumLab.exe con configuracion desktop segura."
    )
    parser.add_argument(
        "--mode",
        choices=["development", "production"],
        default=os.getenv("PERFUMLAB_DESKTOP_MODE", "development"),
    )
    parser.add_argument(
        "--api-url",
        default=None,
        help="URL publica de FastAPI. En production debe ser https:// y no localhost.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=float(os.getenv("PERFUMLAB_API_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)),
    )
    parser.add_argument(
        "--clean",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Elimina build/PerfumLab y dist/PerfumLab antes de construir.",
    )
    return parser.parse_args()


def _remove_controlled(path: Path) -> None:
    root = PROJECT_ROOT.resolve()
    target = path.resolve()
    if target == root or not target.is_relative_to(root):
        raise RuntimeError(f"Ruta fuera del proyecto: {target}")
    if target.exists():
        shutil.rmtree(target)


if __name__ == "__main__":
    raise SystemExit(main())
