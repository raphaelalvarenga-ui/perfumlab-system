from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import get_settings


def login(client, username, password):
    return client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def crear_token(payload):
    settings = get_settings()
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def token_base(usuario_id, token_version=0):
    now = datetime.now(timezone.utc)
    return {
        "sub": str(usuario_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=30)).timestamp()),
        "ver": token_version,
    }


def test_login_correcto_y_me(public_client, admin_user):
    response = login(public_client, "ADMIN_TEST", "admin-password")

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]

    response = public_client.get("/api/v1/auth/me", headers=bearer(data["access_token"]))
    assert response.status_code == 200
    me = response.json()
    assert me["id"] == admin_user["id"]
    assert me["username"] == "admin_test"
    assert me["rol"] == "ADMINISTRADOR"
    assert "password" not in me
    assert "password_hash" not in me


def test_login_usuario_o_password_invalidos(public_client):
    response = login(public_client, "admin_test", "password-malo")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["detail"] == "Usuario o contrasena incorrectos."

    response = login(public_client, "no_existe", "password-malo")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["detail"] == "Usuario o contrasena incorrectos."


def test_login_usuario_inactivo(client, public_client, vendedor_user):
    response = client.delete(f"/api/v1/usuarios/{vendedor_user['id']}")
    assert response.status_code == 200

    response = login(public_client, vendedor_user["username"], vendedor_user["password"])
    assert response.status_code == 403
    assert response.json()["detail"] == "El usuario esta inactivo."


def test_token_invalido_manipulado_vencido_sin_sub_y_version(
    public_client,
    vendedor_user,
):
    response = public_client.get("/api/v1/auth/me")
    assert response.status_code == 401

    response = public_client.get("/api/v1/auth/me", headers=bearer("token-invalido"))
    assert response.status_code == 401

    settings = get_settings()
    token_manipulado = jwt.encode(
        token_base(vendedor_user["id"], 0),
        "secret-distinto-para-test-manipulado-32-bytes",
        algorithm=settings.jwt_algorithm,
    )
    response = public_client.get("/api/v1/auth/me", headers=bearer(token_manipulado))
    assert response.status_code == 401

    now = datetime.now(timezone.utc)
    token_vencido = crear_token(
        {
            "sub": str(vendedor_user["id"]),
            "iat": int((now - timedelta(hours=2)).timestamp()),
            "exp": int((now - timedelta(hours=1)).timestamp()),
            "ver": 0,
        }
    )
    response = public_client.get("/api/v1/auth/me", headers=bearer(token_vencido))
    assert response.status_code == 401
    assert response.json()["detail"] == "El token ha expirado."

    token_sin_sub = crear_token(
        {
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=30)).timestamp()),
            "ver": 0,
        }
    )
    response = public_client.get("/api/v1/auth/me", headers=bearer(token_sin_sub))
    assert response.status_code == 401

    token_version_incorrecta = crear_token(token_base(vendedor_user["id"], 999))
    response = public_client.get(
        "/api/v1/auth/me",
        headers=bearer(token_version_incorrecta),
    )
    assert response.status_code == 401


def test_change_password_invalida_token_anterior(client, public_client, admin_user):
    old_token = login(public_client, admin_user["username"], admin_user["password"]).json()[
        "access_token"
    ]

    response = public_client.post(
        "/api/v1/auth/change-password",
        headers=bearer(old_token),
        json={
            "password_actual": admin_user["password"],
            "password_nueva": "admin-password-nueva",
        },
    )
    assert response.status_code == 204
    assert response.text == ""

    response = public_client.get("/api/v1/auth/me", headers=bearer(old_token))
    assert response.status_code == 401

    response = login(public_client, admin_user["username"], "admin-password-nueva")
    assert response.status_code == 200
    new_token = response.json()["access_token"]
    assert new_token != old_token
    assert public_client.get("/api/v1/auth/me", headers=bearer(new_token)).status_code == 200

    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "password_actual": "incorrecta",
            "password_nueva": "otra-password-nueva",
        },
    )
    assert response.status_code == 401


def test_password_no_aparece_en_errores_422(client):
    response = client.post(
        "/api/v1/usuarios",
        json={
            "nombre": "Usuario Seguro",
            "username": "seguro",
            "password": "corta",
            "rol": "VENDEDOR",
        },
    )

    assert response.status_code == 422
    assert "corta" not in response.text
