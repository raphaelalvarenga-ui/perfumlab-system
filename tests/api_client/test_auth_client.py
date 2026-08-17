import httpx
import pytest

from app.api_client import (
    ApiAuthenticationError,
    ApiConnectionError,
    ApiPermissionError,
    UserSession,
)

from .conftest import form_data, json_response


def test_login_success_reads_token_and_me(make_api_client):
    requests = []

    def handler(request):
        requests.append(request)
        if request.url.path == "/api/v1/auth/login":
            assert form_data(request) == {"username": "admin", "password": "secret"}
            assert "authorization" not in request.headers
            return json_response(200, {"access_token": "token-123", "token_type": "bearer"})
        assert request.url.path == "/api/v1/auth/me"
        assert request.headers["authorization"] == "Bearer token-123"
        return json_response(
            200,
            {
                "id": 1,
                "nombre": "Admin",
                "username": "admin",
                "rol": "ADMINISTRADOR",
                "activo": True,
            },
        )

    client = make_api_client(handler)

    session = client.auth.login("admin", "secret")

    assert session.access_token == "token-123"
    assert session.usuario_id == 1
    assert session.is_admin
    assert [request.url.path for request in requests] == [
        "/api/v1/auth/login",
        "/api/v1/auth/me",
    ]


def test_login_401_does_not_store_token(make_api_client):
    client = make_api_client(
        lambda _request: json_response(401, {"detail": "Invalid credentials"})
    )

    with pytest.raises(ApiAuthenticationError) as error:
        client.auth.login("bad", "bad")

    assert "Usuario o contrasena incorrectos" in str(error.value)
    assert client.session.access_token is None


def test_inactive_user_cannot_enter(make_api_client):
    def handler(request):
        if request.url.path == "/api/v1/auth/login":
            return json_response(200, {"access_token": "token-123", "token_type": "bearer"})
        return json_response(
            200,
            {
                "id": 2,
                "nombre": "Inactivo",
                "username": "inactivo",
                "rol": "VENDEDOR",
                "activo": False,
            },
        )

    client = make_api_client(handler)

    with pytest.raises(ApiAuthenticationError) as error:
        client.auth.login("inactivo", "secret")

    assert "inactivo" in str(error.value)
    assert client.session.access_token is None


def test_logout_clears_in_memory_session(make_api_client):
    session = UserSession(access_token="token", usuario_id=1, rol="ADMINISTRADOR")
    client = make_api_client(lambda _request: json_response(200), session=session)

    client.auth.logout()

    assert session.access_token is None
    assert not session.is_authenticated


def test_401_with_token_clears_session_and_calls_callback(make_api_client):
    session = UserSession(access_token="expired", usuario_id=1, rol="ADMINISTRADOR")
    client = make_api_client(
        lambda _request: json_response(401, {"detail": "Token invalid"}),
        session=session,
    )
    called = []
    client.on_authentication_error = called.append

    with pytest.raises(ApiAuthenticationError):
        client.request("GET", "/api/v1/productos")

    assert session.access_token is None
    assert called and isinstance(called[0], ApiAuthenticationError)


def test_403_is_permission_error(make_api_client):
    client = make_api_client(lambda _request: json_response(403, {"detail": "Forbidden"}))

    with pytest.raises(ApiPermissionError):
        client.request("DELETE", "/api/v1/productos/1")


def test_connection_refused_is_connection_error(make_api_client):
    def handler(request):
        raise httpx.ConnectError("refused", request=request)

    client = make_api_client(handler)

    with pytest.raises(ApiConnectionError):
        client.auth.me()
