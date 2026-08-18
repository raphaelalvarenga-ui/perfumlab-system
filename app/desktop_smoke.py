from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from app.api_client import (
    ApiAuthenticationError,
    ApiPermissionError,
    get_api_client,
    reset_api_client,
)


def run_desktop_smoke() -> int:
    result: dict[str, Any] = {
        "ok": False,
        "checks": {},
        "created": {
            "categoria_ids": [],
            "producto_ids": [],
            "cliente_ids": [],
            "movimiento_ids": [],
            "venta_ids": [],
            "factura_ids": [],
        },
    }
    output_path = _output_path()

    try:
        _run_checks(result)
    except Exception as error:
        result["error"] = {
            "type": type(error).__name__,
            "message": str(error),
        }
        _write_result(output_path, result)
        reset_api_client()
        return 1

    result["ok"] = True
    _write_result(output_path, result)
    reset_api_client()
    return 0


def _run_checks(result: dict[str, Any]) -> None:
    admin_username = _required_env("PERFUMLAB_SMOKE_ADMIN_USERNAME")
    admin_password = _required_env("PERFUMLAB_SMOKE_ADMIN_PASSWORD")
    vendor_username = _required_env("PERFUMLAB_SMOKE_VENDOR_USERNAME")
    vendor_password = _required_env("PERFUMLAB_SMOKE_VENDOR_PASSWORD")
    prefix = os.getenv("PERFUMLAB_SMOKE_PREFIX", "TEST-PACK")
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")

    api = get_api_client()
    api.health_check(include_db=True)
    _mark(result, "api_health")

    try:
        api.auth.login(admin_username, admin_password + "-wrong")
    except ApiAuthenticationError:
        _mark(result, "bad_password_rejected")
    else:
        raise RuntimeError("La API acepto una contrasena incorrecta.")

    api.auth.login(admin_username, admin_password)
    _mark(result, "admin_login")

    api.productos.listar_todos(activo=None)
    _mark(result, "productos_list")
    api.clientes.listar_todos(activo=None)
    _mark(result, "clientes_list")

    categoria = api.categorias.crear(
        {"nombre": f"{prefix} Categoria {stamp}", "activo": True}
    )
    categoria_id = int(categoria["id"])
    result["created"]["categoria_ids"].append(categoria_id)
    _mark(result, "categoria_create")

    producto = api.productos.crear(
        {
            "sku": f"TPACK-{stamp}",
            "nombre": f"{prefix} Producto {stamp}",
            "marca": "Perfum Lab Smoke",
            "descripcion": "Smoke test desktop packaging",
            "categoria_id": categoria_id,
            "costo": "10.00",
            "precio": "25.00",
            "stock_actual": 10,
            "stock_minimo": 1,
            "ml": 50,
            "activo": True,
        }
    )
    producto_id = int(producto["id"])
    result["created"]["producto_ids"].append(producto_id)
    _mark(result, "producto_create")

    movimiento = api.inventario.registrar_entrada(
        producto_id,
        2,
        f"{prefix} entrada smoke",
    )
    result["created"]["movimiento_ids"].append(int(movimiento["id"]))
    api.inventario.listar_movimientos_todos(producto_id=producto_id)
    _mark(result, "inventario_admin")

    api.auth.logout()
    _mark(result, "admin_logout_before_vendor")

    api.auth.login(vendor_username, vendor_password)
    _mark(result, "vendor_login")

    cliente = api.clientes.crear(
        {
            "nombre": f"{prefix} Cliente {stamp}",
            "correo": f"test-pack-{stamp}@example.com",
            "telefono": "9999-0000",
            "direccion": "Smoke desktop",
            "activo": True,
        }
    )
    cliente_id = int(cliente["id"])
    result["created"]["cliente_ids"].append(cliente_id)
    _mark(result, "cliente_vendor_create")

    venta = api.ventas.crear(
        cliente_id=cliente_id,
        productos=[{"producto_id": producto_id, "cantidad": 1}],
    )
    venta_id = int(venta["id"])
    result["created"]["venta_ids"].append(venta_id)
    _mark(result, "venta_vendor_create")

    factura = api.facturas.emitir(venta_id)
    result["created"]["factura_ids"].append(int(factura["id"]))
    _mark(result, "factura_vendor_create")

    _expect_permission_error(
        result,
        "vendor_cannot_inventory_manual",
        lambda: api.inventario.registrar_ajuste(
            producto_id,
            20,
            f"{prefix} ajuste no permitido",
        ),
    )
    _expect_permission_error(
        result,
        "vendor_cannot_edit_products",
        lambda: api.productos.actualizar(producto_id, {"nombre": f"{prefix} Editado"}),
    )
    _expect_permission_error(
        result,
        "vendor_cannot_reportes",
        lambda: api.reportes.resumen(),
    )
    _expect_permission_error(
        result,
        "vendor_cannot_cancel_sale",
        lambda: api.ventas.anular(venta_id, f"{prefix} anulacion no permitida"),
    )

    api.auth.logout()
    if api.session.access_token is not None:
        raise RuntimeError("El JWT sigue en memoria despues del logout.")
    _mark(result, "jwt_memory_cleared_after_logout")

    api.auth.login(admin_username, admin_password)
    api.reportes.resumen()
    _mark(result, "reportes_admin")

    venta_cancelable = api.ventas.crear(
        cliente_id=cliente_id,
        productos=[{"producto_id": producto_id, "cantidad": 1}],
    )
    venta_cancelable_id = int(venta_cancelable["id"])
    result["created"]["venta_ids"].append(venta_cancelable_id)
    api.ventas.anular(venta_cancelable_id, f"{prefix} anulacion admin smoke")
    _mark(result, "venta_admin_cancel")

    api.productos.eliminar(producto_id)
    api.clientes.eliminar(cliente_id)
    api.categorias.eliminar(categoria_id)
    _mark(result, "soft_delete_temp_records")

    api.auth.logout()
    if api.session.access_token is not None:
        raise RuntimeError("El JWT sigue en memoria al finalizar el smoke.")
    _mark(result, "final_logout")


def _expect_permission_error(
    result: dict[str, Any],
    check_name: str,
    action: Callable[[], Any],
) -> None:
    try:
        action()
    except ApiPermissionError:
        _mark(result, check_name)
        return
    raise RuntimeError(f"El permiso esperado no fue rechazado: {check_name}")


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} no esta configurada para el smoke.")
    return value


def _mark(result: dict[str, Any], name: str) -> None:
    result["checks"][name] = True


def _output_path() -> Path:
    raw_path = os.getenv("PERFUMLAB_SMOKE_OUTPUT")
    if raw_path:
        return Path(raw_path)
    return Path.cwd() / "desktop-smoke-result.json"


def _write_result(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
