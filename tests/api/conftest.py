import pytest
import sys
from fastapi.testclient import TestClient
from pathlib import Path
from sqlalchemy import create_engine
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
from app.models.orm.usuario import UsuarioORM
from app.models.tipos import RolUsuario
from app.services.auth_service import AuthService


@pytest.fixture()
def api_context():
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

    db = testing_session_local()
    try:
        admin = UsuarioORM(
            nombre="Admin Test",
            username="admin_test",
            email="admin@test.local",
            password_hash=hash_password("admin-password"),
            rol=RolUsuario.ADMINISTRADOR,
            activo=True,
            token_version=0,
        )
        vendedor = UsuarioORM(
            nombre="Vendedor Test",
            username="vendedor_test",
            email="vendedor@test.local",
            password_hash=hash_password("vendedor-password"),
            rol=RolUsuario.VENDEDOR,
            activo=True,
            token_version=0,
        )
        db.add_all([admin, vendedor])
        db.commit()
        db.refresh(admin)
        db.refresh(vendedor)
        auth_service = AuthService(db)
        admin_token = auth_service.create_access_token(admin)
        vendedor_token = auth_service.create_access_token(vendedor)
        contexto = {
            "session_factory": testing_session_local,
            "admin_user": {
                "id": admin.id,
                "username": admin.username,
                "password": "admin-password",
            },
            "vendedor_user": {
                "id": vendedor.id,
                "username": vendedor.username,
                "password": "vendedor-password",
            },
            "admin_token": admin_token,
            "vendedor_token": vendedor_token,
            "admin_headers": {"Authorization": f"Bearer {admin_token}"},
            "vendedor_headers": {"Authorization": f"Bearer {vendedor_token}"},
        }
    finally:
        db.close()

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield contexto
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(api_context):
    with TestClient(app) as test_client:
        test_client.headers.update(api_context["admin_headers"])
        yield test_client


@pytest.fixture()
def public_client(api_context):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db_session(api_context):
    db = api_context["session_factory"]()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def admin_user(api_context):
    return api_context["admin_user"]


@pytest.fixture()
def vendedor_user(api_context):
    return api_context["vendedor_user"]


@pytest.fixture()
def admin_token(api_context):
    return api_context["admin_token"]


@pytest.fixture()
def vendedor_token(api_context):
    return api_context["vendedor_token"]


@pytest.fixture()
def admin_headers(api_context):
    return api_context["admin_headers"]


@pytest.fixture()
def vendedor_headers(api_context):
    return api_context["vendedor_headers"]
