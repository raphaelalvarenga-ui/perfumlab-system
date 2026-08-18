from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import bindparam, text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXE = PROJECT_ROOT / "dist" / "PerfumLab" / "PerfumLab.exe"

sys.path.insert(0, str(PROJECT_ROOT))

import app.models.orm  # noqa: E402,F401
from app.core.security import hash_password  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402
from app.models.orm.usuario import UsuarioORM  # noqa: E402
from app.models.tipos import RolUsuario  # noqa: E402


def main() -> int:
    args = parse_args()
    exe_path = Path(args.exe_path).resolve()
    if not exe_path.exists():
        raise SystemExit(f"No se encontro el ejecutable: {exe_path}")
    if SessionLocal is None:
        raise SystemExit("DATABASE_URL no esta configurada para preparar el smoke.")

    api_url = args.api_url.rstrip("/")
    _check_api_health(api_url)

    prefix = args.prefix
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_path = PROJECT_ROOT / ".test_tmp" / f"desktop-smoke-{stamp}.json"
    admin_username = f"test_pack_admin_{stamp}"
    vendor_username = f"test_pack_vendor_{stamp}"
    admin_password = f"TmpAdmin{stamp}!"
    vendor_password = f"TmpVendor{stamp}!"

    json_hash_before = _json_hashes()
    result: dict[str, Any] = {}

    try:
        _create_smoke_users(
            admin_username=admin_username,
            admin_password=admin_password,
            vendor_username=vendor_username,
            vendor_password=vendor_password,
            stamp=stamp,
        )

        env = os.environ.copy()
        env.update(
            {
                "PERFUMLAB_DESKTOP_SMOKE": "1",
                "PERFUMLAB_DESKTOP_MODE": args.mode,
                "PERFUMLAB_API_URL": api_url,
                "PERFUMLAB_API_TIMEOUT_SECONDS": str(args.timeout_seconds),
                "PERFUMLAB_SMOKE_ADMIN_USERNAME": admin_username,
                "PERFUMLAB_SMOKE_ADMIN_PASSWORD": admin_password,
                "PERFUMLAB_SMOKE_VENDOR_USERNAME": vendor_username,
                "PERFUMLAB_SMOKE_VENDOR_PASSWORD": vendor_password,
                "PERFUMLAB_SMOKE_PREFIX": prefix,
                "PERFUMLAB_SMOKE_OUTPUT": str(output_path),
            }
        )

        completed = subprocess.run(
            [str(exe_path)],
            cwd=exe_path.parent,
            env=env,
            timeout=args.process_timeout_seconds,
            check=False,
        )
        if output_path.exists():
            result = json.loads(output_path.read_text(encoding="utf-8"))
        if completed.returncode != 0:
            raise SystemExit(
                f"El smoke del EXE fallo con codigo {completed.returncode}. "
                f"Detalle: {output_path}"
            )
        if not result.get("ok"):
            raise SystemExit(f"El smoke del EXE reporto error. Detalle: {output_path}")
    finally:
        _cleanup_smoke_data(result, [admin_username, vendor_username])

    json_hash_after = _json_hashes()
    if json_hash_before != json_hash_after:
        raise SystemExit("database/json cambio durante el smoke del EXE.")

    print(
        json.dumps(
            {
                "ok": True,
                "exe": str(exe_path),
                "api_url": api_url,
                "output": str(output_path),
                "checks": result.get("checks", {}),
                "json_hash_unchanged": True,
            },
            indent=2,
            ensure_ascii=True,
        )
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ejecuta smoke real contra PerfumLab.exe.")
    parser.add_argument("--exe-path", default=str(DEFAULT_EXE))
    parser.add_argument("--api-url", default=os.getenv("PERFUMLAB_API_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--mode", choices=["development", "production"], default="development")
    parser.add_argument("--prefix", default="TEST-PACK")
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=float(os.getenv("PERFUMLAB_API_TIMEOUT_SECONDS", "10")),
    )
    parser.add_argument("--process-timeout-seconds", type=int, default=180)
    return parser.parse_args()


def _check_api_health(api_url: str) -> None:
    with httpx.Client(base_url=api_url, timeout=10) as client:
        health = client.get("/api/v1/health")
        health.raise_for_status()
        db_health = client.get("/api/v1/health/db")
        db_health.raise_for_status()


def _create_smoke_users(
    *,
    admin_username: str,
    admin_password: str,
    vendor_username: str,
    vendor_password: str,
    stamp: str,
) -> None:
    db = SessionLocal()
    try:
        db.add_all(
            [
                UsuarioORM(
                    nombre=f"TEST-PACK Admin {stamp}",
                    username=admin_username,
                    email=f"{admin_username}@example.com",
                    password_hash=hash_password(admin_password),
                    rol=RolUsuario.ADMINISTRADOR,
                    activo=True,
                    token_version=0,
                ),
                UsuarioORM(
                    nombre=f"TEST-PACK Vendor {stamp}",
                    username=vendor_username,
                    email=f"{vendor_username}@example.com",
                    password_hash=hash_password(vendor_password),
                    rol=RolUsuario.VENDEDOR,
                    activo=True,
                    token_version=0,
                ),
            ]
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _cleanup_smoke_data(result: dict[str, Any], usernames: list[str]) -> None:
    created = result.get("created", {}) if isinstance(result, dict) else {}
    venta_ids = _ids(created.get("venta_ids"))
    factura_ids = _ids(created.get("factura_ids"))
    producto_ids = _ids(created.get("producto_ids"))
    cliente_ids = _ids(created.get("cliente_ids"))
    categoria_ids = _ids(created.get("categoria_ids"))
    movimiento_ids = _ids(created.get("movimiento_ids"))

    db = SessionLocal()
    try:
        _delete_in(db, "facturas", "id", factura_ids)
        _delete_in(db, "facturas", "venta_id", venta_ids)
        _delete_in(db, "detalle_ventas", "venta_id", venta_ids)
        _delete_in(db, "movimientos_inventario", "id", movimiento_ids)
        _delete_in(db, "movimientos_inventario", "producto_id", producto_ids)
        _delete_in(db, "ventas", "id", venta_ids)
        _delete_in(db, "producto_notas", "producto_id", producto_ids)
        _delete_in(db, "producto_acordes", "producto_id", producto_ids)
        _delete_in(db, "productos", "id", producto_ids)
        _delete_in(db, "clientes", "id", cliente_ids)
        _delete_in(db, "categorias", "id", categoria_ids)
        _delete_in(db, "usuarios", "username", usernames)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _delete_in(db, table: str, column: str, values: list[Any]) -> None:
    clean_values = [value for value in values if value not in (None, "")]
    if not clean_values:
        return
    statement = text(f"DELETE FROM {table} WHERE {column} IN :values").bindparams(
        bindparam("values", expanding=True)
    )
    db.execute(statement, {"values": clean_values})


def _ids(raw_values: Any) -> list[int]:
    if not isinstance(raw_values, list):
        return []
    values = []
    for value in raw_values:
        try:
            values.append(int(value))
        except (TypeError, ValueError):
            continue
    return values


def _json_hashes() -> dict[str, str]:
    json_dir = PROJECT_ROOT / "database" / "json"
    if not json_dir.exists():
        return {}
    hashes = {}
    for path in sorted(json_dir.glob("*.json")):
        hashes[str(path.relative_to(PROJECT_ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


if __name__ == "__main__":
    raise SystemExit(main())
