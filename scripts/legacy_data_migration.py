from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.engine import URL
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session

import app.models.orm  # noqa: F401
from app.core.config import get_settings
from app.database.session import SessionLocal
from app.models.orm.categoria import CategoriaORM
from app.models.orm.cliente import ClienteORM
from app.models.orm.detalle_venta import DetalleVentaORM
from app.models.orm.factura import FacturaORM
from app.models.orm.movimiento_inventario import MovimientoInventarioORM
from app.models.orm.producto import ProductoORM
from app.models.orm.usuario import UsuarioORM
from app.models.orm.venta import VentaORM
from app.models.tipos import EstadoFactura, EstadoVenta, TipoMovimientoInventario


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEGACY_SOURCE = PROJECT_ROOT / "database" / "json"
REPORTS_DIR = PROJECT_ROOT / "migration_reports"
BACKUPS_DIR = PROJECT_ROOT / "backups"

LEGACY_TABLES = {
    "categorias": "categorias.json",
    "productos": "productos.json",
    "clientes": "clientes.json",
    "ventas": "ventas.json",
    "detalle_venta": "detalle_venta.json",
    "movimientos_inventario": "movimientos_inventario.json",
    "facturas": "facturas.json",
    "usuarios": "usuarios.json",
}

POSTGRES_TABLES = {
    "categorias": CategoriaORM,
    "productos": ProductoORM,
    "clientes": ClienteORM,
    "ventas": VentaORM,
    "detalle_ventas": DetalleVentaORM,
    "movimientos_inventario": MovimientoInventarioORM,
    "facturas": FacturaORM,
    "usuarios": UsuarioORM,
}

MIGRATED_TABLES = [
    "categorias",
    "clientes",
    "productos",
    "ventas",
    "detalle_venta",
    "movimientos_inventario",
    "facturas",
]

STATE_VENTA_MAP = {
    "completada": EstadoVenta.COMPLETADA,
    "completado": EstadoVenta.COMPLETADA,
    "completed": EstadoVenta.COMPLETADA,
    "anulada": EstadoVenta.ANULADA,
    "anulado": EstadoVenta.ANULADA,
    "cancelada": EstadoVenta.ANULADA,
    "cancelado": EstadoVenta.ANULADA,
    "cancelled": EstadoVenta.ANULADA,
}

STATE_FACTURA_MAP = {
    "emitida": EstadoFactura.EMITIDA,
    "emitido": EstadoFactura.EMITIDA,
    "activa": EstadoFactura.EMITIDA,
    "activo": EstadoFactura.EMITIDA,
    "anulada": EstadoFactura.ANULADA,
    "anulado": EstadoFactura.ANULADA,
    "cancelada": EstadoFactura.ANULADA,
    "cancelado": EstadoFactura.ANULADA,
}

MOVEMENT_TYPE_MAP = {
    "entrada": TipoMovimientoInventario.ENTRADA,
    "salida": TipoMovimientoInventario.SALIDA,
    "ajuste": TipoMovimientoInventario.AJUSTE,
}


class MigrationSafetyError(RuntimeError):
    pass


@dataclass
class Problem:
    severity: str
    table: str
    message: str
    record_id: Any | None = None


@dataclass
class TableAudit:
    count: int = 0
    min_id: int | None = None
    max_id: int | None = None
    duplicate_ids: list[int] = field(default_factory=list)
    gaps: list[int] = field(default_factory=list)
    missing_fields: dict[str, int] = field(default_factory=dict)
    invalid_types: dict[str, int] = field(default_factory=dict)


@dataclass
class LegacyAudit:
    source_path: str
    route_resolution: str
    tables: dict[str, TableAudit]
    problems: list[Problem]
    candidate_sets: list[dict[str, Any]] = field(default_factory=list)

    @property
    def info(self) -> list[Problem]:
        return [problem for problem in self.problems if problem.severity == "INFO"]

    @property
    def warnings(self) -> list[Problem]:
        return [problem for problem in self.problems if problem.severity == "WARNING"]

    @property
    def critical(self) -> list[Problem]:
        return [problem for problem in self.problems if problem.severity == "CRITICAL"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "route_resolution": self.route_resolution,
            "tables": {name: asdict(audit) for name, audit in self.tables.items()},
            "counts": {name: audit.count for name, audit in self.tables.items()},
            "problems": [asdict(problem) for problem in self.problems],
            "candidate_sets": self.candidate_sets,
        }


@dataclass
class MigrationPlan:
    categorias: list[dict[str, Any]] = field(default_factory=list)
    clientes: list[dict[str, Any]] = field(default_factory=list)
    productos: list[dict[str, Any]] = field(default_factory=list)
    ventas: list[dict[str, Any]] = field(default_factory=list)
    detalle_ventas: list[dict[str, Any]] = field(default_factory=list)
    movimientos_inventario: list[dict[str, Any]] = field(default_factory=list)
    facturas: list[dict[str, Any]] = field(default_factory=list)
    mappings: dict[str, Any] = field(default_factory=dict)
    warnings: list[Problem] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        return {
            "categorias": len(self.categorias),
            "clientes": len(self.clientes),
            "productos": len(self.productos),
            "ventas": len(self.ventas),
            "detalle_ventas": len(self.detalle_ventas),
            "movimientos_inventario": len(self.movimientos_inventario),
            "facturas": len(self.facturas),
            "usuarios": 0,
        }


def resolve_source(source: str | None = None) -> Path:
    return Path(source).expanduser().resolve() if source else LEGACY_SOURCE.resolve()


def describe_route_resolution() -> str:
    return (
        "app.database.json_storage.JSON_DIR = "
        "Path(__file__).resolve().parents[2] / 'database' / 'json'. "
        "En codigo fuente esto apunta a la raiz del repo; en el exe one-dir de "
        "PyInstaller apunta a dist/PerfumLab/_internal/database/json."
    )


def discover_candidate_sets(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    json_names = set(LEGACY_TABLES.values())
    grouped: dict[Path, dict[str, Any]] = {}
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [
            item
            for item in dirs
            if item not in {".git", ".venv", ".pytest_cache", ".test_tmp", "migration_reports"}
        ]
        matching = [file_name for file_name in files if file_name in json_names]
        if not matching:
            continue
        base = Path(root)
        entry = grouped.setdefault(
            base,
            {
                "path": str(base),
                "files": {},
                "total_records": 0,
                "looks_like_source": False,
                "looks_like_build_copy": False,
                "looks_like_backup": False,
                "looks_like_real_data": False,
            },
        )
        for file_name in sorted(matching):
            path = base / file_name
            count, valid = count_json_records(path)
            stat = path.stat()
            entry["files"][file_name] = {
                "path": str(path),
                "size_bytes": stat.st_size,
                "modified_at": stat.st_mtime,
                "modified_at_iso": datetime.fromtimestamp(
                    stat.st_mtime,
                    timezone.utc,
                ).isoformat(),
                "record_count": count,
                "valid_json_list": valid,
            }
            entry["total_records"] += count if valid else 0

        normalized = str(base).replace("\\", "/").lower()
        entry["looks_like_source"] = base.resolve() == (project_root / "database" / "json").resolve()
        entry["looks_like_build_copy"] = "/dist/" in normalized or "/build/" in normalized
        entry["looks_like_backup"] = "/backups/" in normalized
        entry["looks_like_real_data"] = entry["total_records"] > 0
    return sorted(grouped.values(), key=lambda item: item["path"])


def count_json_records(path: Path) -> tuple[int, bool]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0, False
    return (len(data), True) if isinstance(data, list) else (0, False)


def load_legacy_data(source: Path) -> dict[str, list[dict[str, Any]]]:
    data: dict[str, list[dict[str, Any]]] = {}
    for table, file_name in LEGACY_TABLES.items():
        path = source / file_name
        if not path.exists():
            data[table] = []
            continue
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise MigrationSafetyError(f"{file_name} no contiene JSON valido.") from error
        if not isinstance(loaded, list):
            raise MigrationSafetyError(f"{file_name} debe contener una lista.")
        data[table] = loaded
    return data


def audit_legacy_source(
    source: Path,
    *,
    candidate_sets: list[dict[str, Any]] | None = None,
) -> LegacyAudit:
    problems: list[Problem] = []
    data = load_legacy_data(source)
    tables = {
        table: audit_table_shape(table, rows, problems)
        for table, rows in data.items()
    }

    audit_categories(data, problems)
    audit_clients(data, problems)
    audit_products(data, problems)
    audit_sales(data, problems)
    audit_sale_details(data, problems)
    audit_inventory(data, problems)
    audit_invoices(data, problems)
    audit_users(data, problems)
    audit_stock_history(data, problems)

    return LegacyAudit(
        source_path=str(source),
        route_resolution=describe_route_resolution(),
        tables=tables,
        problems=problems,
        candidate_sets=candidate_sets or [],
    )


def audit_table_shape(
    table: str,
    rows: list[Any],
    problems: list[Problem],
) -> TableAudit:
    ids = []
    missing_fields: dict[str, int] = {}
    invalid_types: dict[str, int] = {}
    required = required_fields_for(table)

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            add_problem(
                problems,
                "CRITICAL",
                table,
                "Registro no es objeto JSON.",
                index,
            )
            continue
        for field_name in required:
            if field_name not in row:
                missing_fields[field_name] = missing_fields.get(field_name, 0) + 1
        row_id = parse_int(row.get("id"))
        if row_id is None:
            invalid_types["id"] = invalid_types.get("id", 0) + 1
        else:
            ids.append(row_id)

    duplicates = sorted(value for value in set(ids) if ids.count(value) > 1)
    for duplicate_id in duplicates:
        add_problem(problems, "CRITICAL", table, "ID duplicado.", duplicate_id)

    gaps: list[int] = []
    if ids:
        id_set = set(ids)
        gaps = [
            value
            for value in range(min(id_set), max(id_set) + 1)
            if value not in id_set
        ]
        if gaps:
            add_problem(
                problems,
                "INFO",
                table,
                f"IDs con gaps: {len(gaps)}.",
            )

    for field_name, count in missing_fields.items():
        add_problem(
            problems,
            "WARNING",
            table,
            f"Campo faltante {field_name}: {count} registros.",
        )
    for field_name, count in invalid_types.items():
        add_problem(
            problems,
            "CRITICAL",
            table,
            f"Tipo invalido para {field_name}: {count} registros.",
        )

    return TableAudit(
        count=len(rows),
        min_id=min(ids) if ids else None,
        max_id=max(ids) if ids else None,
        duplicate_ids=duplicates,
        gaps=gaps,
        missing_fields=missing_fields,
        invalid_types=invalid_types,
    )


def required_fields_for(table: str) -> list[str]:
    return {
        "categorias": ["id", "nombre", "activo"],
        "productos": [
            "id",
            "sku",
            "nombre",
            "marca",
            "categoria_id",
            "costo",
            "precio",
            "stock_actual",
            "stock_minimo",
            "activo",
        ],
        "clientes": ["id", "nombre", "activo"],
        "ventas": ["id", "total", "estado"],
        "detalle_venta": ["id", "venta_id", "producto_id", "cantidad"],
        "movimientos_inventario": [
            "id",
            "producto_id",
            "cantidad",
            "stock_anterior",
            "stock_nuevo",
            "motivo",
        ],
        "facturas": ["id", "venta_id", "total"],
        "usuarios": ["id"],
    }.get(table, ["id"])


def audit_categories(data: dict[str, list[dict[str, Any]]], problems: list[Problem]) -> None:
    names: dict[str, int] = {}
    for row in iter_dicts(data["categorias"]):
        row_id = row.get("id")
        name = clean_text(row.get("nombre"))
        if not name:
            add_problem(problems, "CRITICAL", "categorias", "Nombre vacio.", row_id)
        else:
            key = name.lower()
            if key in names:
                add_problem(
                    problems,
                    "CRITICAL",
                    "categorias",
                    "Nombre duplicado case-insensitive.",
                    row_id,
                )
            names[key] = parse_int(row_id) or 0
        if parse_bool(row.get("activo")) is None:
            add_problem(problems, "WARNING", "categorias", "Activo invalido.", row_id)


def audit_products(data: dict[str, list[dict[str, Any]]], problems: list[Problem]) -> None:
    category_ids = valid_ids(data["categorias"])
    skus: dict[str, int] = {}
    for row in iter_dicts(data["productos"]):
        row_id = row.get("id")
        sku = clean_text(row.get("sku"))
        if not sku:
            add_problem(problems, "CRITICAL", "productos", "SKU vacio.", row_id)
        else:
            key = sku.lower()
            if key in skus:
                add_problem(
                    problems,
                    "CRITICAL",
                    "productos",
                    "SKU duplicado case-insensitive.",
                    row_id,
                )
            skus[key] = parse_int(row_id) or 0
        if not clean_text(row.get("nombre")):
            add_problem(problems, "CRITICAL", "productos", "Nombre vacio.", row_id)
        if not clean_text(row.get("marca")):
            add_problem(problems, "CRITICAL", "productos", "Marca vacia.", row_id)
        categoria_id = parse_int(row.get("categoria_id"))
        if categoria_id is None or categoria_id not in category_ids:
            add_problem(
                problems,
                "CRITICAL",
                "productos",
                "Categoria inexistente.",
                row_id,
            )
        for money_field in ["costo", "precio"]:
            value = parse_decimal(row.get(money_field))
            if value is None:
                add_problem(problems, "CRITICAL", "productos", f"{money_field} invalido.", row_id)
            elif value < 0:
                add_problem(problems, "CRITICAL", "productos", f"{money_field} negativo.", row_id)
        for int_field in ["stock_actual", "stock_minimo"]:
            value = parse_int(row.get(int_field))
            if value is None:
                add_problem(problems, "CRITICAL", "productos", f"{int_field} invalido.", row_id)
            elif value < 0:
                add_problem(problems, "CRITICAL", "productos", f"{int_field} negativo.", row_id)
        ml = row.get("ml")
        if ml not in (None, ""):
            ml_value = parse_int(ml)
            if ml_value is None or ml_value <= 0:
                add_problem(problems, "WARNING", "productos", "ml invalido.", row_id)
        if parse_bool(row.get("activo")) is None:
            add_problem(problems, "WARNING", "productos", "Activo invalido.", row_id)


def audit_clients(data: dict[str, list[dict[str, Any]]], problems: list[Problem]) -> None:
    emails: dict[str, int] = {}
    for row in iter_dicts(data["clientes"]):
        row_id = row.get("id")
        if not clean_text(row.get("nombre")):
            add_problem(problems, "CRITICAL", "clientes", "Nombre vacio.", row_id)
        correo = clean_text(row.get("correo"))
        if not correo:
            if "correo" in row:
                add_problem(problems, "INFO", "clientes", "Correo vacio se migrara como NULL.", row_id)
            continue
        if "@" not in correo or "." not in correo.split("@")[-1]:
            add_problem(problems, "WARNING", "clientes", "Correo invalido.", row_id)
        key = correo.lower()
        if key in emails:
            add_problem(
                problems,
                "CRITICAL",
                "clientes",
                "Correo duplicado case-insensitive.",
                row_id,
            )
        emails[key] = parse_int(row_id) or 0


def audit_sales(data: dict[str, list[dict[str, Any]]], problems: list[Problem]) -> None:
    client_ids = valid_ids(data["clientes"])
    sale_ids = valid_ids(data["ventas"])
    details_by_sale = group_by_int(data["detalle_venta"], "venta_id")
    for row in iter_dicts(data["ventas"]):
        row_id = row.get("id")
        state = normalize_sale_state(row.get("estado"))
        if state is None:
            add_problem(problems, "CRITICAL", "ventas", "Estado desconocido.", row_id)
        cliente_id = parse_int(row.get("cliente_id"))
        if cliente_id is not None and cliente_id not in client_ids:
            add_problem(
                problems,
                "WARNING",
                "ventas",
                "cliente_id inexistente; se preservara cliente_nombre si existe.",
                row_id,
            )
        total = parse_decimal(row.get("total"))
        if total is None:
            add_problem(problems, "CRITICAL", "ventas", "Total invalido.", row_id)
        elif total < 0:
            add_problem(problems, "CRITICAL", "ventas", "Total negativo.", row_id)
        if parse_int(row.get("usuario_id")) is not None:
            add_problem(
                problems,
                "INFO",
                "ventas",
                "usuario_id legado se migrara como NULL.",
                row_id,
            )
        if parse_int(row_id) in sale_ids and not details_by_sale.get(parse_int(row_id)):
            add_problem(problems, "WARNING", "ventas", "Venta sin detalles.", row_id)


def audit_sale_details(
    data: dict[str, list[dict[str, Any]]],
    problems: list[Problem],
) -> None:
    sale_ids = valid_ids(data["ventas"])
    product_ids = valid_ids(data["productos"])
    for row in iter_dicts(data["detalle_venta"]):
        row_id = row.get("id")
        venta_id = parse_int(row.get("venta_id"))
        producto_id = parse_int(row.get("producto_id"))
        if venta_id not in sale_ids:
            add_problem(problems, "CRITICAL", "detalle_venta", "venta_id inexistente.", row_id)
        if producto_id not in product_ids:
            add_problem(problems, "CRITICAL", "detalle_venta", "producto_id inexistente.", row_id)
        cantidad = parse_int(row.get("cantidad"))
        if cantidad is None or cantidad <= 0:
            add_problem(problems, "CRITICAL", "detalle_venta", "cantidad invalida.", row_id)
        precio = parse_decimal(row.get("precio_unitario"))
        subtotal = parse_decimal(row.get("subtotal"))
        if precio is not None and precio < 0:
            add_problem(problems, "CRITICAL", "detalle_venta", "precio_unitario negativo.", row_id)
        if subtotal is not None and subtotal < 0:
            add_problem(problems, "CRITICAL", "detalle_venta", "subtotal negativo.", row_id)
        if precio is not None and subtotal is not None and cantidad:
            expected = (precio * Decimal(cantidad)).quantize(Decimal("0.01"))
            if subtotal.quantize(Decimal("0.01")) != expected:
                add_problem(
                    problems,
                    "WARNING",
                    "detalle_venta",
                    "Subtotal no coincide con precio_unitario * cantidad.",
                    row_id,
                )


def audit_inventory(data: dict[str, list[dict[str, Any]]], problems: list[Problem]) -> None:
    product_ids = valid_ids(data["productos"])
    for row in iter_dicts(data["movimientos_inventario"]):
        row_id = row.get("id")
        producto_id = parse_int(row.get("producto_id"))
        if producto_id not in product_ids:
            add_problem(
                problems,
                "CRITICAL",
                "movimientos_inventario",
                "producto_id inexistente.",
                row_id,
            )
        if normalize_movement_type(row.get("tipo") or row.get("tipo_movimiento")) is None:
            add_problem(
                problems,
                "CRITICAL",
                "movimientos_inventario",
                "Tipo desconocido.",
                row_id,
            )
        for field_name in ["cantidad", "stock_anterior", "stock_nuevo"]:
            value = parse_int(row.get(field_name))
            if value is None:
                add_problem(
                    problems,
                    "CRITICAL",
                    "movimientos_inventario",
                    f"{field_name} invalido.",
                    row_id,
                )
            elif field_name == "cantidad" and value <= 0:
                add_problem(
                    problems,
                    "CRITICAL",
                    "movimientos_inventario",
                    "cantidad invalida.",
                    row_id,
                )
            elif field_name != "cantidad" and value < 0:
                add_problem(
                    problems,
                    "CRITICAL",
                    "movimientos_inventario",
                    f"{field_name} negativo.",
                    row_id,
                )
        if not clean_text(row.get("motivo")):
            add_problem(
                problems,
                "CRITICAL",
                "movimientos_inventario",
                "motivo vacio.",
                row_id,
            )


def audit_stock_history(
    data: dict[str, list[dict[str, Any]]],
    problems: list[Problem],
) -> None:
    movements_by_product = group_by_int(data["movimientos_inventario"], "producto_id")
    products_by_id = {
        parse_int(row.get("id")): row
        for row in iter_dicts(data["productos"])
        if parse_int(row.get("id")) is not None
    }
    for product_id, movements in movements_by_product.items():
        product = products_by_id.get(product_id)
        if product is None or not movements:
            continue
        epoch = datetime.min.replace(tzinfo=timezone.utc)
        last = sorted(
            movements,
            key=lambda row: (parse_datetime(row.get("fecha")) or epoch, parse_int(row.get("id")) or 0),
        )[-1]
        product_stock = parse_int(product.get("stock_actual"))
        history_stock = parse_int(last.get("stock_nuevo"))
        if product_stock is not None and history_stock is not None and product_stock != history_stock:
            add_problem(
                problems,
                "WARNING",
                "productos",
                (
                    f"stock_actual ({product_stock}) no coincide con ultimo "
                    f"movimiento ({history_stock})."
                ),
                product_id,
            )


def audit_invoices(data: dict[str, list[dict[str, Any]]], problems: list[Problem]) -> None:
    sale_ids = valid_ids(data["ventas"])
    sales_by_id = {
        parse_int(row.get("id")): row
        for row in iter_dicts(data["ventas"])
        if parse_int(row.get("id")) is not None
    }
    invoices_by_sale: dict[int, int] = {}
    numbers: dict[str, int] = {}
    for row in iter_dicts(data["facturas"]):
        row_id = row.get("id")
        venta_id = parse_int(row.get("venta_id"))
        if venta_id not in sale_ids:
            add_problem(problems, "CRITICAL", "facturas", "Factura sin venta valida.", row_id)
        elif venta_id in invoices_by_sale:
            add_problem(
                problems,
                "CRITICAL",
                "facturas",
                "Dos facturas para una misma venta.",
                row_id,
            )
        invoices_by_sale[venta_id or -1] = parse_int(row_id) or 0

        numero = clean_text(row.get("numero") or row.get("numero_factura"))
        if not numero:
            add_problem(problems, "CRITICAL", "facturas", "Numero vacio.", row_id)
        elif numero.lower() in numbers:
            add_problem(problems, "CRITICAL", "facturas", "Numero duplicado.", row_id)
        numbers[numero.lower()] = parse_int(row_id) or 0

        total = parse_decimal(row.get("total"))
        if total is None:
            add_problem(problems, "CRITICAL", "facturas", "Total invalido.", row_id)
        elif total < 0:
            add_problem(problems, "CRITICAL", "facturas", "Total negativo.", row_id)

        sale = sales_by_id.get(venta_id)
        state = normalize_invoice_state(row.get("estado"))
        if state is None and "estado" in row:
            add_problem(problems, "CRITICAL", "facturas", "Estado desconocido.", row_id)
        if sale and normalize_sale_state(sale.get("estado")) == EstadoVenta.ANULADA:
            if state is None or state == EstadoFactura.EMITIDA:
                add_problem(
                    problems,
                    "WARNING",
                    "facturas",
                    "Venta anulada con factura activa.",
                    row_id,
                )


def audit_users(data: dict[str, list[dict[str, Any]]], problems: list[Problem]) -> None:
    if not data["usuarios"]:
        add_problem(problems, "INFO", "usuarios", "0 usuarios legado migrados.")
        return
    add_problem(
        problems,
        "WARNING",
        "usuarios",
        "Usuarios legacy presentes; se auditan pero no se migran automaticamente.",
    )


def build_migration_plan(
    source: Path,
    audit: LegacyAudit | None = None,
) -> MigrationPlan:
    data = load_legacy_data(source)
    audit = audit or audit_legacy_source(source)
    if audit.critical:
        raise MigrationSafetyError(
            f"Auditoria contiene {len(audit.critical)} problemas CRITICAL."
        )

    plan = MigrationPlan()
    categories_by_id = normalize_categories(data["categorias"])
    clients_by_id = normalize_clients(data["clientes"])
    products_by_id = normalize_products(data["productos"])
    sales_by_id = normalize_sales(data["ventas"], clients_by_id)
    details_by_id = normalize_details(data["detalle_venta"], products_by_id)
    movements_by_id = normalize_movements(data["movimientos_inventario"])
    invoices_by_id = normalize_invoices(data["facturas"], sales_by_id)

    plan.categorias = list(categories_by_id.values())
    plan.clientes = list(clients_by_id.values())
    plan.productos = list(products_by_id.values())
    plan.ventas = list(sales_by_id.values())
    plan.detalle_ventas = list(details_by_id.values())
    plan.movimientos_inventario = list(movements_by_id.values())
    plan.facturas = list(invoices_by_id.values())
    plan.warnings = audit.warnings
    plan.mappings = {
        "usuarios": "No se migran usuarios legacy; auditoria historica queda en NULL.",
        "venta_usuario_id": "usuario_id legado se migra como NULL.",
        "movimiento_usuario_id": "usuario_id legado se migra como NULL.",
        "factura_usuario_id": "usuario_id legado se migra como NULL.",
    }
    return plan


def normalize_categories(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    result = {}
    for row in iter_dicts(rows):
        row_id = require_int(row.get("id"), "categoria.id")
        result[row_id] = {
            "id": row_id,
            "nombre": clean_text(row.get("nombre")),
            "activo": bool_from_legacy(row.get("activo"), default=True),
            "created_at": parse_datetime(row.get("fecha_creacion")),
            "updated_at": parse_datetime(row.get("fecha_actualizacion")),
        }
    return result


def normalize_clients(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    result = {}
    for row in iter_dicts(rows):
        row_id = require_int(row.get("id"), "cliente.id")
        correo = clean_text(row.get("correo"))
        result[row_id] = {
            "id": row_id,
            "nombre": clean_text(row.get("nombre")),
            "correo": correo.lower() if correo else None,
            "telefono": clean_text(row.get("telefono")) or None,
            "direccion": clean_text(row.get("direccion")) or None,
            "activo": bool_from_legacy(row.get("activo"), default=True),
            "created_at": parse_datetime(row.get("fecha_creacion")),
            "updated_at": parse_datetime(row.get("fecha_actualizacion")),
        }
    return result


def normalize_products(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    result = {}
    for row in iter_dicts(rows):
        row_id = require_int(row.get("id"), "producto.id")
        result[row_id] = {
            "id": row_id,
            "sku": clean_text(row.get("sku")),
            "nombre": clean_text(row.get("nombre")),
            "marca": clean_text(row.get("marca")),
            "descripcion": clean_text(row.get("descripcion")) or None,
            "categoria_id": require_int(row.get("categoria_id"), "producto.categoria_id"),
            "costo": require_decimal(row.get("costo"), "producto.costo"),
            "precio": require_decimal(row.get("precio"), "producto.precio"),
            "stock_actual": require_int(row.get("stock_actual"), "producto.stock_actual"),
            "stock_minimo": require_int(row.get("stock_minimo"), "producto.stock_minimo"),
            "ml": parse_int(row.get("ml")) if row.get("ml") not in (None, "") else None,
            "imagen": clean_text(row.get("imagen")) or None,
            "activo": bool_from_legacy(row.get("activo"), default=True),
            "created_at": parse_datetime(row.get("fecha_creacion")),
            "updated_at": parse_datetime(row.get("fecha_actualizacion")),
        }
    return result


def normalize_sales(
    rows: list[dict[str, Any]],
    clients_by_id: dict[int, dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    result = {}
    for row in iter_dicts(rows):
        row_id = require_int(row.get("id"), "venta.id")
        cliente_id = parse_int(row.get("cliente_id"))
        cliente_nombre = clean_text(row.get("cliente_nombre") or row.get("cliente"))
        if cliente_id in clients_by_id:
            cliente_nombre = clients_by_id[cliente_id]["nombre"]
        if not cliente_nombre:
            cliente_nombre = "Cliente mostrador"
        total = require_decimal(row.get("total"), "venta.total")
        result[row_id] = {
            "id": row_id,
            "cliente_id": cliente_id if cliente_id in clients_by_id else None,
            "cliente_nombre": cliente_nombre,
            "usuario_id": None,
            "estado": normalize_sale_state(row.get("estado")) or EstadoVenta.COMPLETADA,
            "subtotal": require_decimal(row.get("subtotal"), "venta.subtotal")
            if row.get("subtotal") is not None
            else total,
            "total": total,
            "created_at": parse_datetime(row.get("fecha") or row.get("created_at")),
            "anulada_at": parse_datetime(row.get("fecha_anulacion") or row.get("anulada_at")),
            "motivo_anulacion": clean_text(row.get("motivo_anulacion")) or None,
            "anulada_por_usuario_id": None,
        }
    return result


def normalize_details(
    rows: list[dict[str, Any]],
    products_by_id: dict[int, dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    result = {}
    for row in iter_dicts(rows):
        row_id = require_int(row.get("id"), "detalle.id")
        producto_id = require_int(row.get("producto_id"), "detalle.producto_id")
        product = products_by_id[producto_id]
        cantidad = require_int(row.get("cantidad"), "detalle.cantidad")
        precio = require_decimal(
            row.get("precio_unitario") if row.get("precio_unitario") is not None else product["precio"],
            "detalle.precio_unitario",
        )
        subtotal = require_decimal(
            row.get("subtotal") if row.get("subtotal") is not None else precio * Decimal(cantidad),
            "detalle.subtotal",
        )
        result[row_id] = {
            "id": row_id,
            "venta_id": require_int(row.get("venta_id"), "detalle.venta_id"),
            "producto_id": producto_id,
            "producto_sku": clean_text(row.get("producto_sku")) or product["sku"],
            "producto_nombre": clean_text(row.get("producto_nombre")) or product["nombre"],
            "precio_unitario": precio,
            "cantidad": cantidad,
            "subtotal": subtotal,
            "created_at": parse_datetime(row.get("fecha") or row.get("created_at")),
        }
    return result


def normalize_movements(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    result = {}
    for row in iter_dicts(rows):
        row_id = require_int(row.get("id"), "movimiento.id")
        result[row_id] = {
            "id": row_id,
            "producto_id": require_int(row.get("producto_id"), "movimiento.producto_id"),
            "tipo": normalize_movement_type(row.get("tipo") or row.get("tipo_movimiento"))
            or TipoMovimientoInventario.AJUSTE,
            "cantidad": require_int(row.get("cantidad"), "movimiento.cantidad"),
            "stock_anterior": require_int(row.get("stock_anterior"), "movimiento.stock_anterior"),
            "stock_nuevo": require_int(row.get("stock_nuevo"), "movimiento.stock_nuevo"),
            "motivo": clean_text(row.get("motivo")),
            "usuario_id": None,
            "created_at": parse_datetime(row.get("fecha") or row.get("created_at")),
        }
    return result


def normalize_invoices(
    rows: list[dict[str, Any]],
    sales_by_id: dict[int, dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    result = {}
    for row in iter_dicts(rows):
        row_id = require_int(row.get("id"), "factura.id")
        venta_id = require_int(row.get("venta_id"), "factura.venta_id")
        sale = sales_by_id[venta_id]
        total = require_decimal(row.get("total"), "factura.total")
        result[row_id] = {
            "id": row_id,
            "numero": clean_text(row.get("numero") or row.get("numero_factura"))
            or f"FAC-{venta_id:06d}",
            "venta_id": venta_id,
            "usuario_id": None,
            "cliente_nombre": clean_text(row.get("cliente_nombre")) or sale["cliente_nombre"],
            "subtotal": require_decimal(row.get("subtotal"), "factura.subtotal")
            if row.get("subtotal") is not None
            else total,
            "total": total,
            "estado": normalize_invoice_state(row.get("estado")) or EstadoFactura.EMITIDA,
            "created_at": parse_datetime(row.get("fecha") or row.get("created_at")),
            "anulada_at": parse_datetime(row.get("fecha_anulacion") or row.get("anulada_at")),
            "motivo_anulacion": clean_text(row.get("motivo_anulacion")) or None,
            "anulada_por_usuario_id": None,
        }
    return result


def check_postgres_conflicts(db: Session, plan: MigrationPlan) -> list[Problem]:
    conflicts: list[Problem] = []
    check_id_conflicts(db, CategoriaORM, "categorias", plan.categorias, conflicts)
    check_id_conflicts(db, ClienteORM, "clientes", plan.clientes, conflicts)
    check_id_conflicts(db, ProductoORM, "productos", plan.productos, conflicts)
    check_id_conflicts(db, VentaORM, "ventas", plan.ventas, conflicts)
    check_id_conflicts(db, DetalleVentaORM, "detalle_ventas", plan.detalle_ventas, conflicts)
    check_id_conflicts(
        db,
        MovimientoInventarioORM,
        "movimientos_inventario",
        plan.movimientos_inventario,
        conflicts,
    )
    check_id_conflicts(db, FacturaORM, "facturas", plan.facturas, conflicts)

    for categoria in plan.categorias:
        exists = db.scalar(
            select(CategoriaORM.id).where(
                func.lower(CategoriaORM.nombre) == categoria["nombre"].lower()
            )
        )
        if exists is not None and exists != categoria["id"]:
            add_problem(conflicts, "CRITICAL", "categorias", "Nombre ya existe en PostgreSQL.", categoria["id"])

    for producto in plan.productos:
        exists = db.scalar(
            select(ProductoORM.id).where(func.lower(ProductoORM.sku) == producto["sku"].lower())
        )
        if exists is not None and exists != producto["id"]:
            add_problem(conflicts, "CRITICAL", "productos", "SKU ya existe en PostgreSQL.", producto["id"])

    for cliente in plan.clientes:
        correo = cliente.get("correo")
        if not correo:
            continue
        exists = db.scalar(
            select(ClienteORM.id).where(func.lower(ClienteORM.correo) == correo.lower())
        )
        if exists is not None and exists != cliente["id"]:
            add_problem(conflicts, "CRITICAL", "clientes", "Correo ya existe en PostgreSQL.", cliente["id"])

    for factura in plan.facturas:
        existing_number = db.scalar(
            select(FacturaORM.id).where(FacturaORM.numero == factura["numero"])
        )
        if existing_number is not None and existing_number != factura["id"]:
            add_problem(conflicts, "CRITICAL", "facturas", "Numero ya existe en PostgreSQL.", factura["id"])
        existing_sale = db.scalar(
            select(FacturaORM.id).where(FacturaORM.venta_id == factura["venta_id"])
        )
        if existing_sale is not None and existing_sale != factura["id"]:
            add_problem(conflicts, "CRITICAL", "facturas", "Venta ya tiene factura en PostgreSQL.", factura["id"])
    return conflicts


def check_id_conflicts(
    db: Session,
    model,
    table: str,
    rows: list[dict[str, Any]],
    conflicts: list[Problem],
) -> None:
    ids = [row["id"] for row in rows]
    if not ids:
        return
    existing = set(db.scalars(select(model.id).where(model.id.in_(ids))).all())
    for row_id in sorted(existing):
        add_problem(conflicts, "CRITICAL", table, "ID colisiona en PostgreSQL.", row_id)


def apply_migration(db: Session, plan: MigrationPlan) -> dict[str, Any]:
    try:
        for row in plan.categorias:
            db.add(CategoriaORM(**without_none_timestamps(row)))
        for row in plan.clientes:
            db.add(ClienteORM(**without_none_timestamps(row)))
        for row in plan.productos:
            db.add(ProductoORM(**without_none_timestamps(row)))
        for row in plan.ventas:
            db.add(VentaORM(**without_none_timestamps(row)))
        for row in plan.detalle_ventas:
            db.add(DetalleVentaORM(**without_none_timestamps(row)))
        for row in plan.movimientos_inventario:
            db.add(MovimientoInventarioORM(**without_none_timestamps(row)))
        for row in plan.facturas:
            db.add(FacturaORM(**without_none_timestamps(row)))
        db.flush()
        sequence_results = update_sequences(db)
        db.commit()
        return {"sequences": sequence_results}
    except Exception:
        db.rollback()
        raise


def without_none_timestamps(row: dict[str, Any]) -> dict[str, Any]:
    clean = dict(row)
    for key in ["created_at", "updated_at", "anulada_at"]:
        if clean.get(key) is None:
            clean.pop(key, None)
    return clean


def update_sequences(db: Session) -> dict[str, dict[str, Any]]:
    results = {}
    bind = db.get_bind()
    dialect = bind.dialect.name
    for table in [
        "categorias",
        "productos",
        "clientes",
        "ventas",
        "detalle_ventas",
        "movimientos_inventario",
        "facturas",
    ]:
        max_id = db.scalar(text(f"SELECT COALESCE(MAX(id), 0) FROM {table}"))
        if dialect == "postgresql":
            db.execute(
                text(
                    f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table}', 'id'),
                        GREATEST(:max_id, 1),
                        :has_rows
                    )
                    """
                ),
                {"max_id": int(max_id or 0), "has_rows": bool(max_id)},
            )
        results[table] = {
            "max_id": int(max_id or 0),
            "next_id_should_be_gt": int(max_id or 0),
        }
    return results


def postgres_counts(db: Session) -> dict[str, int]:
    counts = {}
    for name, model in POSTGRES_TABLES.items():
        counts[name] = int(db.scalar(select(func.count()).select_from(model)) or 0)
    return counts


def post_migration_checks(db: Session) -> dict[str, int]:
    checks = {}
    checks["sku_duplicados"] = int(
        db.scalar(
            text(
                """
                SELECT COUNT(*) FROM (
                    SELECT lower(sku) FROM productos GROUP BY lower(sku) HAVING COUNT(*) > 1
                ) q
                """
            )
        )
        or 0
    )
    checks["emails_duplicados"] = int(
        db.scalar(
            text(
                """
                SELECT COUNT(*) FROM (
                    SELECT lower(correo) FROM clientes
                    WHERE correo IS NOT NULL
                    GROUP BY lower(correo) HAVING COUNT(*) > 1
                ) q
                """
            )
        )
        or 0
    )
    checks["facturas_duplicadas_por_venta"] = int(
        db.scalar(
            text(
                """
                SELECT COUNT(*) FROM (
                    SELECT venta_id FROM facturas GROUP BY venta_id HAVING COUNT(*) > 1
                ) q
                """
            )
        )
        or 0
    )
    checks["stock_negativo"] = int(
        db.scalar(text("SELECT COUNT(*) FROM productos WHERE stock_actual < 0 OR stock_minimo < 0"))
        or 0
    )
    checks["ventas_total_negativo"] = int(
        db.scalar(text("SELECT COUNT(*) FROM ventas WHERE total < 0 OR subtotal < 0")) or 0
    )
    checks["detalles_cantidad_invalida"] = int(
        db.scalar(text("SELECT COUNT(*) FROM detalle_ventas WHERE cantidad <= 0")) or 0
    )
    checks["movimientos_stock_negativo"] = int(
        db.scalar(
            text(
                """
                SELECT COUNT(*) FROM movimientos_inventario
                WHERE cantidad <= 0 OR stock_anterior < 0 OR stock_nuevo < 0
                """
            )
        )
        or 0
    )
    fk_queries = [
        """
        SELECT COUNT(*) FROM productos p
        LEFT JOIN categorias c ON c.id = p.categoria_id
        WHERE c.id IS NULL
        """,
        """
        SELECT COUNT(*) FROM ventas v
        LEFT JOIN clientes c ON c.id = v.cliente_id
        WHERE v.cliente_id IS NOT NULL AND c.id IS NULL
        """,
        """
        SELECT COUNT(*) FROM detalle_ventas d
        LEFT JOIN ventas v ON v.id = d.venta_id
        WHERE v.id IS NULL
        """,
        """
        SELECT COUNT(*) FROM detalle_ventas d
        LEFT JOIN productos p ON p.id = d.producto_id
        WHERE p.id IS NULL
        """,
        """
        SELECT COUNT(*) FROM movimientos_inventario m
        LEFT JOIN productos p ON p.id = m.producto_id
        WHERE p.id IS NULL
        """,
        """
        SELECT COUNT(*) FROM facturas f
        LEFT JOIN ventas v ON v.id = f.venta_id
        WHERE v.id IS NULL
        """,
    ]
    checks["foreign_keys_rotas"] = sum(int(db.scalar(text(query)) or 0) for query in fk_queries)
    return checks


def run_migration(
    *,
    source: Path,
    apply: bool,
    require_pg_backup: bool = True,
) -> dict[str, Any]:
    if SessionLocal is None:
        raise MigrationSafetyError("DATABASE_URL no esta configurado.")

    started = time.monotonic()
    candidates = discover_candidate_sets(PROJECT_ROOT)
    audit = audit_legacy_source(source, candidate_sets=candidates)

    db = SessionLocal()
    try:
        before = postgres_counts(db)
        if audit.critical:
            report = {
                "source_path": str(source),
                "mode": "apply" if apply else "dry-run",
                "counts_json": {name: audit.tables[name].count for name in LEGACY_TABLES},
                "postgres_counts_before": before,
                "records_to_insert": {},
                "warnings": [asdict(problem) for problem in audit.warnings],
                "critical_errors": [asdict(problem) for problem in audit.critical],
                "conflicts": [],
                "mappings": {},
                "sequence_targets": {},
                "candidate_sets": candidates,
                "result": "blocked",
            }
            path = write_report("dry-run", report)
            report["report_path"] = str(path)
            raise MigrationSafetyError(
                f"Migracion bloqueada por problemas CRITICAL. Reporte: {path}"
            )

        plan = build_migration_plan(source, audit)
        conflicts = check_postgres_conflicts(db, plan)
        report = {
            "source_path": str(source),
            "mode": "apply" if apply else "dry-run",
            "counts_json": {name: audit.tables[name].count for name in LEGACY_TABLES},
            "postgres_counts_before": before,
            "records_to_insert": plan.counts(),
            "warnings": [asdict(problem) for problem in audit.warnings],
            "critical_errors": [asdict(problem) for problem in audit.critical],
            "conflicts": [asdict(problem) for problem in conflicts],
            "mappings": plan.mappings,
            "sequence_targets": sequence_targets(plan),
            "candidate_sets": candidates,
            "result": "not-run",
        }

        if audit.critical or conflicts:
            report["result"] = "blocked"
            path = write_report("dry-run", report)
            report["report_path"] = str(path)
            raise MigrationSafetyError(
                f"Migracion bloqueada por problemas CRITICAL o conflictos. Reporte: {path}"
            )

        if not apply:
            after = postgres_counts(db)
            report["postgres_counts_after"] = after
            report["postgres_counts_unchanged"] = before == after
            report["result"] = "ok"
            path = write_report("dry-run", report)
            report["report_path"] = str(path)
            return report

        json_backup = backup_json_source(source)
        report["json_backup"] = json_backup
        if require_pg_backup:
            report["postgres_backup"] = backup_postgres()
        apply_result = apply_migration(db, plan)
        after = postgres_counts(db)
        report["postgres_counts_after"] = after
        report["inserted_counts"] = plan.counts()
        report["sequences"] = apply_result["sequences"]
        report["post_checks"] = post_migration_checks(db)
        report["duration_seconds"] = round(time.monotonic() - started, 3)
        report["result"] = "ok"
        path = write_report("apply", report)
        report["report_path"] = str(path)
        return report
    finally:
        db.close()


def sequence_targets(plan: MigrationPlan) -> dict[str, int]:
    return {
        "categorias": max_id(plan.categorias),
        "clientes": max_id(plan.clientes),
        "productos": max_id(plan.productos),
        "ventas": max_id(plan.ventas),
        "detalle_ventas": max_id(plan.detalle_ventas),
        "movimientos_inventario": max_id(plan.movimientos_inventario),
        "facturas": max_id(plan.facturas),
    }


def max_id(rows: list[dict[str, Any]]) -> int:
    return max([int(row["id"]) for row in rows], default=0)


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def write_report(kind: str, report: dict[str, Any]) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{kind}-{timestamp()}.json"
    safe_report = json.loads(json.dumps(report, default=json_default))
    path.write_text(json.dumps(safe_report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def backup_json_source(source: Path) -> dict[str, Any]:
    backup_dir = BACKUPS_DIR / f"legacy-json-{timestamp()}"
    backup_dir.mkdir(parents=True, exist_ok=False)
    files = {}
    for file_name in LEGACY_TABLES.values():
        original = source / file_name
        backup = backup_dir / file_name
        shutil.copy2(original, backup)
        original_hash = sha256_file(original)
        backup_hash = sha256_file(backup)
        files[file_name] = {
            "original": str(original),
            "backup": str(backup),
            "original_sha256": original_hash,
            "backup_sha256": backup_hash,
            "match": original_hash == backup_hash,
        }
        if original_hash != backup_hash:
            raise MigrationSafetyError(f"Backup JSON no coincide para {file_name}.")
    return {"path": str(backup_dir), "files": files}


def backup_postgres() -> dict[str, Any]:
    settings = get_settings()
    if not settings.database_url:
        raise MigrationSafetyError("DATABASE_URL no esta configurado para pg_dump.")
    pg_dump = find_pg_dump()
    if pg_dump is None:
        raise MigrationSafetyError("pg_dump no esta disponible en PATH ni rutas conocidas.")
    url = make_url(settings.database_url)
    if not url.get_backend_name().startswith("postgresql"):
        raise MigrationSafetyError("pg_dump requiere una DATABASE_URL PostgreSQL.")

    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    output = BACKUPS_DIR / f"postgres-before-json-migration-{timestamp()}.dump"
    command, env = pg_dump_command(pg_dump, url, output)
    completed = subprocess.run(
        command,
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
    )
    if completed.returncode != 0:
        raise MigrationSafetyError("pg_dump fallo; migracion real detenida.")
    return {
        "path": str(output),
        "size_bytes": output.stat().st_size,
        "sha256": sha256_file(output),
    }


def find_pg_dump() -> str | None:
    found = shutil.which("pg_dump")
    if found:
        return found
    for base in [Path("C:/Program Files/PostgreSQL"), Path("C:/Program Files (x86)/PostgreSQL")]:
        if not base.exists():
            continue
        for candidate in sorted(base.glob("*/bin/pg_dump.exe"), reverse=True):
            if candidate.exists():
                return str(candidate)
    return None


def pg_dump_command(pg_dump: str, url: URL, output: Path) -> tuple[list[str], dict[str, str]]:
    env = os.environ.copy()
    if url.password:
        env["PGPASSWORD"] = url.password
    database = str(url.database or "")
    command = [pg_dump, "-Fc", "-f", str(output)]
    if url.host:
        command.extend(["-h", url.host])
    if url.port:
        command.extend(["-p", str(url.port)])
    if url.username:
        command.extend(["-U", url.username])
    command.append(database)
    return command, env


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def print_audit(audit: LegacyAudit) -> None:
    print(f"Fuente JSON: {audit.source_path}")
    print(audit.route_resolution)
    print("")
    labels = {
        "categorias": "Categorias",
        "productos": "Productos",
        "clientes": "Clientes",
        "ventas": "Ventas",
        "detalle_venta": "Detalles",
        "movimientos_inventario": "Movimientos",
        "facturas": "Facturas",
        "usuarios": "Usuarios",
    }
    for table, label in labels.items():
        table_audit = audit.tables[table]
        print(
            f"{label}: {table_audit.count} "
            f"(min_id={table_audit.min_id}, max_id={table_audit.max_id})"
        )
    print("")
    print("Conjuntos JSON candidatos:")
    for candidate in audit.candidate_sets:
        labels_candidate = []
        if candidate["looks_like_source"]:
            labels_candidate.append("codigo fuente")
        if candidate["looks_like_build_copy"]:
            labels_candidate.append("copia build")
        if candidate["looks_like_backup"]:
            labels_candidate.append("backup")
        if candidate["looks_like_real_data"]:
            labels_candidate.append("datos reales")
        if not labels_candidate:
            labels_candidate.append("sin clasificacion")
        print(
            f"- {candidate['path']} | registros={candidate['total_records']} | "
            f"{', '.join(labels_candidate)}"
        )
        for file_name, file_info in sorted(candidate["files"].items()):
            print(
                f"  {file_name}: size={file_info['size_bytes']} bytes, "
                f"count={file_info['record_count']}, "
                f"modified={file_info['modified_at_iso']}"
            )
    print("")
    for severity in ["INFO", "WARNING", "CRITICAL"]:
        items = [problem for problem in audit.problems if problem.severity == severity]
        print(f"{severity}: {len(items)}")
        for problem in items[:50]:
            suffix = f" id={problem.record_id}" if problem.record_id is not None else ""
            print(f"- {problem.table}{suffix}: {problem.message}")


def print_migration_report(report: dict[str, Any]) -> None:
    print(f"Modo: {report['mode']}")
    print(f"Resultado: {report['result']}")
    print(f"Fuente: {report['source_path']}")
    print(f"Reporte: {report.get('report_path')}")
    print(f"Registros a insertar: {report['records_to_insert']}")
    print(f"Conflictos: {len(report['conflicts'])}")
    print(f"Critical: {len(report['critical_errors'])}")
    if "postgres_counts_unchanged" in report:
        print(f"Dry-run sin escrituras: {report['postgres_counts_unchanged']}")
    if "json_backup" in report:
        print(f"Backup JSON: {report['json_backup']['path']}")
    if "postgres_backup" in report:
        print(f"Backup PostgreSQL: {report['postgres_backup']['path']}")


def add_problem(
    problems: list[Problem],
    severity: str,
    table: str,
    message: str,
    record_id: Any | None = None,
) -> None:
    problems.append(Problem(severity=severity, table=table, message=message, record_id=record_id))


def iter_dicts(rows: list[Any]):
    for row in rows:
        if isinstance(row, dict):
            yield row


def valid_ids(rows: list[dict[str, Any]]) -> set[int]:
    return {value for row in iter_dicts(rows) if (value := parse_int(row.get("id"))) is not None}


def group_by_int(rows: list[dict[str, Any]], field_name: str) -> dict[int, list[dict[str, Any]]]:
    result: dict[int, list[dict[str, Any]]] = {}
    for row in iter_dicts(rows):
        key = parse_int(row.get(field_name))
        if key is not None:
            result.setdefault(key, []).append(row)
    return result


def parse_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def require_int(value: Any, field_name: str) -> int:
    parsed = parse_int(value)
    if parsed is None:
        raise MigrationSafetyError(f"{field_name} invalido.")
    return parsed


def parse_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None


def require_decimal(value: Any, field_name: str) -> Decimal:
    parsed = parse_decimal(value)
    if parsed is None:
        raise MigrationSafetyError(f"{field_name} invalido.")
    return parsed


def parse_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value in {1}
    if isinstance(value, str):
        text_value = value.strip().lower()
        if text_value in {"1", "true", "si", "yes", "activo"}:
            return True
        if text_value in {"0", "false", "no", "inactivo"}:
            return False
    return None


def bool_from_legacy(value: Any, *, default: bool) -> bool:
    parsed = parse_bool(value)
    return default if parsed is None else parsed


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def parse_datetime(value: Any) -> datetime | None:
    text_value = clean_text(value)
    if not text_value:
        return None
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"]:
        try:
            return datetime.strptime(text_value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    try:
        parsed = datetime.fromisoformat(text_value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def normalize_sale_state(value: Any) -> EstadoVenta | None:
    return STATE_VENTA_MAP.get(clean_text(value).lower())


def normalize_invoice_state(value: Any) -> EstadoFactura | None:
    text_value = clean_text(value)
    if not text_value:
        return None
    return STATE_FACTURA_MAP.get(text_value.lower())


def normalize_movement_type(value: Any) -> TipoMovimientoInventario | None:
    return MOVEMENT_TYPE_MAP.get(clean_text(value).lower())


def json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return str(value)


def inspect_source_cli(args: argparse.Namespace) -> None:
    source = resolve_source(args.source)
    candidates = discover_candidate_sets(PROJECT_ROOT)
    audit = audit_legacy_source(source, candidate_sets=candidates)
    print_audit(audit)


def migration_cli(args: argparse.Namespace) -> None:
    source = resolve_source(args.source)
    report = run_migration(source=source, apply=args.apply)
    print_migration_report(report)
