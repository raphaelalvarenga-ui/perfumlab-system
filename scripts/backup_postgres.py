from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings  # noqa: E402


def main() -> int:
    args = parse_args()
    settings = get_settings()
    if not settings.database_url:
        raise SystemExit("DATABASE_URL no esta configurada.")

    connection = _parse_postgres_url(settings.database_url)
    pg_dump = shutil.which("pg_dump")
    if pg_dump is None:
        raise SystemExit("pg_dump no esta disponible en PATH.")

    output_dir = (PROJECT_ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = "dump" if args.format == "custom" else "sql"
    output_path = output_dir / f"postgres-backup-{datetime.now():%Y%m%d-%H%M%S}.{suffix}"

    env = os.environ.copy()
    env.update(connection)

    command = [
        pg_dump,
        "--file",
        str(output_path),
        "--no-owner",
        "--no-privileges",
    ]
    if args.format == "custom":
        command.append("--format=custom")
    else:
        command.append("--format=plain")

    subprocess.run(command, env=env, check=True)
    print(f"Backup PostgreSQL generado: {output_path}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genera backup de PostgreSQL con pg_dump.")
    parser.add_argument("--output-dir", default="backups")
    parser.add_argument("--format", choices=["custom", "plain"], default="custom")
    return parser.parse_args()


def _parse_postgres_url(database_url: str) -> dict[str, str]:
    normalized = database_url
    if normalized.startswith("postgresql+psycopg://"):
        normalized = "postgresql://" + normalized.removeprefix("postgresql+psycopg://")
    elif normalized.startswith("postgresql+psycopg2://"):
        normalized = "postgresql://" + normalized.removeprefix("postgresql+psycopg2://")

    parsed = urlparse(normalized)
    if parsed.scheme != "postgresql":
        raise SystemExit("pg_dump requiere una DATABASE_URL PostgreSQL.")
    if not parsed.hostname or not parsed.path.strip("/"):
        raise SystemExit("DATABASE_URL PostgreSQL incompleta.")

    env = {
        "PGHOST": parsed.hostname,
        "PGDATABASE": unquote(parsed.path.strip("/")),
    }
    if parsed.port:
        env["PGPORT"] = str(parsed.port)
    if parsed.username:
        env["PGUSER"] = unquote(parsed.username)
    if parsed.password:
        env["PGPASSWORD"] = unquote(parsed.password)

    query = parse_qs(parsed.query)
    if "sslmode" in query and query["sslmode"]:
        env["PGSSLMODE"] = query["sslmode"][0]

    return env


if __name__ == "__main__":
    raise SystemExit(main())
