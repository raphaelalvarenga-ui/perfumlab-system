import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import legacy_data_migration as legacy


def write_source(tmp_path, data):
    source = tmp_path / "json"
    source.mkdir()
    for table, file_name in legacy.LEGACY_TABLES.items():
        rows = data.get(table, [])
        (source / file_name).write_text(
            json.dumps(rows, indent=2),
            encoding="utf-8",
        )
    return source


def valid_dataset():
    return {
        "categorias": [
            {"id": 10, "nombre": "Fragancias", "activo": True},
        ],
        "clientes": [
            {"id": 20, "nombre": "Cliente Mostrador", "correo": "", "activo": True},
            {
                "id": 21,
                "nombre": "Ana Demo",
                "correo": "ANA@EXAMPLE.COM",
                "activo": True,
            },
        ],
        "productos": [
            {
                "id": 200,
                "sku": "SKU-LEG-001",
                "nombre": "Legacy Eau",
                "marca": "Perfum Lab",
                "categoria_id": 10,
                "costo": "120.10",
                "precio": "220.25",
                "stock_actual": 10,
                "stock_minimo": 2,
                "activo": True,
            },
        ],
        "ventas": [
            {
                "id": 30,
                "cliente_id": 20,
                "usuario_id": 1,
                "estado": "completada",
                "subtotal": "440.50",
                "total": "440.50",
            },
        ],
        "detalle_venta": [
            {
                "id": 40,
                "venta_id": 30,
                "producto_id": 200,
                "precio_unitario": "220.25",
                "cantidad": 2,
                "subtotal": "440.50",
            },
        ],
        "movimientos_inventario": [
            {
                "id": 50,
                "producto_id": 200,
                "tipo": "ENTRADA",
                "cantidad": 10,
                "stock_anterior": 0,
                "stock_nuevo": 10,
                "motivo": "Carga inicial legacy",
                "usuario_id": 1,
            },
        ],
        "facturas": [
            {
                "id": 60,
                "numero": "FAC-LEG-001",
                "venta_id": 30,
                "usuario_id": 1,
                "cliente_nombre": "Cliente Mostrador",
                "subtotal": "440.50",
                "total": "440.50",
                "estado": "emitida",
            },
        ],
        "usuarios": [{"id": 1, "username": "admin_legacy"}],
    }


def test_audit_valid_source_reports_counts_and_non_blocking_infos(workspace_tmp_path):
    source = write_source(workspace_tmp_path, valid_dataset())

    audit = legacy.audit_legacy_source(source)

    assert audit.tables["categorias"].count == 1
    assert audit.tables["productos"].min_id == 200
    assert audit.tables["productos"].max_id == 200
    assert audit.tables["clientes"].count == 2
    assert audit.tables["ventas"].count == 1
    assert audit.tables["detalle_venta"].count == 1
    assert audit.tables["movimientos_inventario"].count == 1
    assert audit.tables["facturas"].count == 1
    assert audit.critical == []
    assert any("usuario_id legado" in problem.message for problem in audit.info)
    assert any(problem.table == "usuarios" for problem in audit.warnings)


def test_audit_detects_invalid_fields_relations_and_duplicates(workspace_tmp_path):
    data = valid_dataset()
    data["categorias"].append({"id": 11, "nombre": "fragancias", "activo": True})
    data["productos"].append(
        {
            "id": 201,
            "sku": "sku-leg-001",
            "nombre": "Duplicado",
            "marca": "Perfum Lab",
            "categoria_id": 999,
            "costo": "-1.00",
            "precio": "abc",
            "stock_actual": -2,
            "stock_minimo": 1,
            "activo": True,
        }
    )
    data["clientes"].append(
        {"id": 22, "nombre": "Correo Duplicado", "correo": "ana@example.com", "activo": True}
    )
    data["detalle_venta"].append(
        {"id": 41, "venta_id": 999, "producto_id": 999, "cantidad": 1}
    )
    data["facturas"].append(
        {
            "id": 61,
            "numero": "FAC-LEG-001",
            "venta_id": 30,
            "cliente_nombre": "Cliente Mostrador",
            "subtotal": "440.50",
            "total": "440.50",
            "estado": "emitida",
        }
    )
    source = write_source(workspace_tmp_path, data)

    audit = legacy.audit_legacy_source(source)
    messages = {(problem.table, problem.message) for problem in audit.critical}

    assert ("categorias", "Nombre duplicado case-insensitive.") in messages
    assert ("productos", "SKU duplicado case-insensitive.") in messages
    assert ("productos", "Categoria inexistente.") in messages
    assert ("productos", "costo negativo.") in messages
    assert ("productos", "precio invalido.") in messages
    assert ("clientes", "Correo duplicado case-insensitive.") in messages
    assert ("detalle_venta", "venta_id inexistente.") in messages
    assert ("detalle_venta", "producto_id inexistente.") in messages
    assert ("facturas", "Numero duplicado.") in messages
