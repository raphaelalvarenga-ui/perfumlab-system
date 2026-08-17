import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app.models.orm  # noqa: F401
from app.core.security import hash_password
from app.database.base import Base
from app.database.session import get_db
from app.main_api import app
from app.models.orm.acorde import AcordeORM
from app.models.orm.categoria import CategoriaORM
from app.models.orm.cliente import ClienteORM
from app.models.orm.detalle_venta import DetalleVentaORM
from app.models.orm.factura import FacturaORM
from app.models.orm.movimiento_inventario import MovimientoInventarioORM
from app.models.orm.nota import NotaORM
from app.models.orm.producto import ProductoORM
from app.models.orm.usuario import UsuarioORM
from app.models.orm.venta import VentaORM
from app.models.tipos import EstadoFactura, EstadoVenta, RolUsuario, TipoMovimientoInventario
from app.services.auth_service import AuthService
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
                "cliente_nombre": "Cliente Mostrador",
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


@pytest.fixture()
def sqlite_session_factory(monkeypatch, workspace_tmp_path):
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(legacy, "SessionLocal", testing_session_local)
    monkeypatch.setattr(legacy, "REPORTS_DIR", workspace_tmp_path / "reports")
    monkeypatch.setattr(legacy, "BACKUPS_DIR", workspace_tmp_path / "backups")
    yield testing_session_local
    Base.metadata.drop_all(bind=engine)


def count_rows(session_factory, model):
    db = session_factory()
    try:
        return int(db.scalar(select(func.count()).select_from(model)) or 0)
    finally:
        db.close()


def test_dry_run_does_not_write_and_reports_records(
    workspace_tmp_path,
    sqlite_session_factory,
):
    source = write_source(workspace_tmp_path, valid_dataset())

    report = legacy.run_migration(source=source, apply=False)

    assert report["result"] == "ok"
    assert report["postgres_counts_unchanged"] is True
    assert report["records_to_insert"] == {
        "categorias": 1,
        "clientes": 2,
        "productos": 1,
        "ventas": 1,
        "detalle_ventas": 1,
        "movimientos_inventario": 1,
        "facturas": 1,
        "usuarios": 0,
    }
    assert count_rows(sqlite_session_factory, CategoriaORM) == 0
    assert count_rows(sqlite_session_factory, ProductoORM) == 0
    assert count_rows(sqlite_session_factory, ClienteORM) == 0
    assert (workspace_tmp_path / "reports").exists()


def test_apply_migrates_entities_preserving_ids_and_values(
    workspace_tmp_path,
    sqlite_session_factory,
):
    source = write_source(workspace_tmp_path, valid_dataset())

    report = legacy.run_migration(
        source=source,
        apply=True,
        require_pg_backup=False,
    )

    assert report["result"] == "ok"
    assert all(file["match"] for file in report["json_backup"]["files"].values())
    db = sqlite_session_factory()
    try:
        categoria = db.get(CategoriaORM, 10)
        cliente_sin_correo = db.get(ClienteORM, 20)
        cliente_con_correo = db.get(ClienteORM, 21)
        producto = db.get(ProductoORM, 200)
        venta = db.get(VentaORM, 30)
        detalle = db.get(DetalleVentaORM, 40)
        movimiento = db.get(MovimientoInventarioORM, 50)
        factura = db.get(FacturaORM, 60)

        assert categoria.nombre == "Fragancias"
        assert cliente_sin_correo.correo is None
        assert cliente_con_correo.correo == "ana@example.com"
        assert producto.precio == Decimal("220.25")
        assert producto.costo == Decimal("120.10")
        assert producto.stock_actual == 10
        assert producto.genero is None
        assert producto.external_provider is None
        assert venta.estado == EstadoVenta.COMPLETADA
        assert venta.usuario_id is None
        assert venta.total == Decimal("440.50")
        assert detalle.producto_id == 200
        assert detalle.subtotal == Decimal("440.50")
        assert movimiento.tipo == TipoMovimientoInventario.ENTRADA
        assert movimiento.usuario_id is None
        assert factura.estado == EstadoFactura.EMITIDA
        assert factura.usuario_id is None
        assert factura.numero == "FAC-LEG-001"
        assert count_rows(sqlite_session_factory, AcordeORM) == 0
        assert count_rows(sqlite_session_factory, NotaORM) == 0
    finally:
        db.close()


def test_apply_leaves_sequences_after_preserved_ids(workspace_tmp_path, sqlite_session_factory):
    source = write_source(workspace_tmp_path, valid_dataset())
    legacy.run_migration(source=source, apply=True, require_pg_backup=False)

    db = sqlite_session_factory()
    try:
        categoria = CategoriaORM(nombre="Nueva Categoria", activo=True)
        db.add(categoria)
        db.flush()
        producto = ProductoORM(
            sku="SKU-NEXT-001",
            nombre="Nuevo Producto",
            marca="Perfum Lab",
            categoria_id=categoria.id,
            costo=Decimal("1.00"),
            precio=Decimal("2.00"),
            stock_actual=0,
            stock_minimo=0,
            activo=True,
        )
        db.add(producto)
        db.flush()

        assert categoria.id > 10
        assert producto.id > 200
    finally:
        db.close()


def test_apply_blocks_invalid_foreign_key_and_leaves_database_empty(
    workspace_tmp_path,
    sqlite_session_factory,
):
    data = valid_dataset()
    data["detalle_venta"][0]["producto_id"] = 999
    source = write_source(workspace_tmp_path, data)

    with pytest.raises(legacy.MigrationSafetyError):
        legacy.run_migration(source=source, apply=True, require_pg_backup=False)

    assert count_rows(sqlite_session_factory, CategoriaORM) == 0
    assert count_rows(sqlite_session_factory, ProductoORM) == 0
    assert count_rows(sqlite_session_factory, VentaORM) == 0
    report_files = list((workspace_tmp_path / "reports").glob("dry-run-*.json"))
    assert report_files
    report = json.loads(report_files[0].read_text(encoding="utf-8"))
    assert report["result"] == "blocked"


def test_duplicate_sku_blocks_dry_run(workspace_tmp_path, sqlite_session_factory):
    data = valid_dataset()
    data["productos"].append(
        {
            "id": 201,
            "sku": "sku-leg-001",
            "nombre": "Duplicado",
            "marca": "Perfum Lab",
            "categoria_id": 10,
            "costo": "10.00",
            "precio": "20.00",
            "stock_actual": 1,
            "stock_minimo": 0,
            "activo": True,
        }
    )
    source = write_source(workspace_tmp_path, data)

    with pytest.raises(legacy.MigrationSafetyError):
        legacy.run_migration(source=source, apply=False)

    assert count_rows(sqlite_session_factory, ProductoORM) == 0


def test_duplicate_invoice_number_blocks_dry_run(workspace_tmp_path, sqlite_session_factory):
    data = valid_dataset()
    data["ventas"].append(
        {
            "id": 31,
            "cliente_id": 21,
            "estado": "completada",
            "subtotal": "220.25",
            "total": "220.25",
        }
    )
    data["detalle_venta"].append(
        {
            "id": 41,
            "venta_id": 31,
            "producto_id": 200,
            "precio_unitario": "220.25",
            "cantidad": 1,
            "subtotal": "220.25",
        }
    )
    data["facturas"].append(
        {
            "id": 61,
            "numero": "FAC-LEG-001",
            "venta_id": 31,
            "cliente_nombre": "Ana Demo",
            "subtotal": "220.25",
            "total": "220.25",
            "estado": "emitida",
        }
    )
    source = write_source(workspace_tmp_path, data)

    with pytest.raises(legacy.MigrationSafetyError):
        legacy.run_migration(source=source, apply=False)

    assert count_rows(sqlite_session_factory, FacturaORM) == 0


def test_movements_are_historical_and_do_not_reapply_stock(
    workspace_tmp_path,
    sqlite_session_factory,
):
    data = valid_dataset()
    data["productos"][0]["stock_actual"] = 10
    data["movimientos_inventario"] = [
        {
            "id": 50,
            "producto_id": 200,
            "tipo": "ENTRADA",
            "cantidad": 10,
            "stock_anterior": 0,
            "stock_nuevo": 10,
            "motivo": "Carga inicial legacy",
        },
        {
            "id": 51,
            "producto_id": 200,
            "tipo": "ENTRADA",
            "cantidad": 5,
            "stock_anterior": 10,
            "stock_nuevo": 15,
            "motivo": "Movimiento historico no aplicado",
            "fecha": "2026-08-01",
        },
    ]
    source = write_source(workspace_tmp_path, data)

    report = legacy.run_migration(source=source, apply=True, require_pg_backup=False)

    db = sqlite_session_factory()
    try:
        producto = db.get(ProductoORM, 200)
        assert producto.stock_actual == 10
        assert count_rows(sqlite_session_factory, MovimientoInventarioORM) == 2
        assert any("stock_actual" in problem["message"] for problem in report["warnings"])
    finally:
        db.close()


def test_migrated_data_serves_authenticated_api_and_reportes(
    workspace_tmp_path,
    sqlite_session_factory,
):
    source = write_source(workspace_tmp_path, valid_dataset())
    legacy.run_migration(source=source, apply=True, require_pg_backup=False)

    db = sqlite_session_factory()
    try:
        admin = UsuarioORM(
            nombre="Admin Migration",
            username="admin_migration",
            email="admin_migration@test.local",
            password_hash=hash_password("admin-password"),
            rol=RolUsuario.ADMINISTRADOR,
            activo=True,
            token_version=0,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        token = AuthService(db).create_access_token(admin)
    finally:
        db.close()

    def override_get_db():
        session = sqlite_session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            client.headers.update({"Authorization": f"Bearer {token}"})
            for path in [
                "/api/v1/categorias",
                "/api/v1/productos",
                "/api/v1/clientes",
                "/api/v1/ventas",
                "/api/v1/facturas",
                "/api/v1/inventario/movimientos",
                "/api/v1/reportes/resumen",
                "/docs",
            ]:
                response = client.get(path)
                assert response.status_code == 200
            resumen = client.get("/api/v1/reportes/resumen").json()
            assert resumen["ventas_completadas"] == 1
            assert resumen["ingresos_totales"] == "440.50"
            assert resumen["unidades_vendidas"] == 2
    finally:
        app.dependency_overrides.pop(get_db, None)
