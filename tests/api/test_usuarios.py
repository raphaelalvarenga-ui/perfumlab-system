def usuario_payload(**overrides):
    data = {
        "nombre": "Usuario Nuevo",
        "username": "usuario_nuevo",
        "email": "usuario.nuevo@example.com",
        "password": "password-segura",
        "rol": "VENDEDOR",
        "activo": True,
    }
    data.update(overrides)
    return data


def crear_usuario(client, **overrides):
    response = client.post("/api/v1/usuarios", json=usuario_payload(**overrides))
    assert response.status_code == 201
    return response.json()


def login(client, username, password):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def assert_no_passwords(data):
    texto = str(data).lower()
    assert "password_hash" not in texto
    assert "password':" not in texto
    assert '"password"' not in texto


def test_admin_crea_admin_y_vendedor_sin_exponer_password(client):
    admin = crear_usuario(
        client,
        nombre="Admin Dos",
        username="AdminDos",
        email=None,
        rol="ADMINISTRADOR",
    )
    vendedor = crear_usuario(
        client,
        nombre="Vendedor Dos",
        username="VendedorDos",
        email="VENDEDOR.DOS@EXAMPLE.COM",
        rol="VENDEDOR",
    )

    assert admin["username"] == "admindos"
    assert admin["email"] is None
    assert admin["rol"] == "ADMINISTRADOR"
    assert vendedor["username"] == "vendedordos"
    assert vendedor["email"] == "vendedor.dos@example.com"
    assert vendedor["rol"] == "VENDEDOR"
    assert_no_passwords(admin)
    assert_no_passwords(vendedor)


def test_vendedor_no_crea_usuarios(client, vendedor_headers):
    response = client.post(
        "/api/v1/usuarios",
        headers=vendedor_headers,
        json=usuario_payload(username="sin_permiso"),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "No tienes permisos para realizar esta accion."


def test_listar_obtener_y_usuario_inexistente(client):
    usuario = crear_usuario(client, username="usuario_listado")

    response = client.get("/api/v1/usuarios", params={"buscar": "listado"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == usuario["id"]
    assert_no_passwords(data)

    response = client.get(f"/api/v1/usuarios/{usuario['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == usuario["id"]
    assert_no_passwords(response.json())

    response = client.get("/api/v1/usuarios/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Usuario no encontrado."


def test_username_y_email_duplicados_case_insensitive(client):
    crear_usuario(
        client,
        username="UsuarioUnico",
        email="unico@example.com",
    )

    response = client.post(
        "/api/v1/usuarios",
        json=usuario_payload(username="usuariounico", email="otro@example.com"),
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Ya existe un usuario con ese username."

    response = client.post(
        "/api/v1/usuarios",
        json=usuario_payload(username="otro_usuario", email="UNICO@EXAMPLE.COM"),
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Ya existe un usuario con ese email."


def test_varios_usuarios_sin_email(client):
    usuario_a = crear_usuario(client, username="sin_email_a", email=None)
    usuario_b = crear_usuario(client, username="sin_email_b", email="")

    assert usuario_a["email"] is None
    assert usuario_b["email"] is None


def test_patch_nombre_username_email_rol_activo_y_soft_delete(client):
    usuario = crear_usuario(client, username="patch_user", email="patch@example.com")

    response = client.patch(
        f"/api/v1/usuarios/{usuario['id']}",
        json={
            "nombre": "Usuario Editado",
            "username": "PatchEditado",
            "email": "",
            "rol": "ADMINISTRADOR",
            "activo": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nombre"] == "Usuario Editado"
    assert data["username"] == "patcheditado"
    assert data["email"] is None
    assert data["rol"] == "ADMINISTRADOR"

    response = client.patch(f"/api/v1/usuarios/{usuario['id']}", json={"password": "x"})
    assert response.status_code == 422

    response = client.delete(f"/api/v1/usuarios/{usuario['id']}")
    assert response.status_code == 200
    assert response.json()["activo"] is False

    response = client.get("/api/v1/usuarios", params={"activo": False})
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_reset_password_invalida_token_anterior(client, public_client, vendedor_user):
    token_viejo = login(
        public_client,
        vendedor_user["username"],
        vendedor_user["password"],
    )

    response = client.post(
        f"/api/v1/usuarios/{vendedor_user['id']}/reset-password",
        json={"password_nueva": "password-vendedor-nueva"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == vendedor_user["id"]
    assert_no_passwords(response.json())

    response = public_client.get("/api/v1/auth/me", headers=bearer(token_viejo))
    assert response.status_code == 401

    token_nuevo = login(
        public_client,
        vendedor_user["username"],
        "password-vendedor-nueva",
    )
    response = public_client.get("/api/v1/auth/me", headers=bearer(token_nuevo))
    assert response.status_code == 200


def test_no_desactivar_ni_convertir_ultimo_admin(client, admin_user):
    response = client.delete(f"/api/v1/usuarios/{admin_user['id']}")
    assert response.status_code == 409
    assert response.json()["detail"] == (
        "No se puede dejar el sistema sin administradores activos."
    )

    response = client.patch(
        f"/api/v1/usuarios/{admin_user['id']}",
        json={"rol": "VENDEDOR"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == (
        "No se puede dejar el sistema sin administradores activos."
    )


def test_puede_desactivar_admin_si_existe_otro_activo(client, admin_user):
    crear_usuario(
        client,
        nombre="Admin Respaldo",
        username="admin_respaldo",
        email=None,
        rol="ADMINISTRADOR",
    )

    response = client.delete(f"/api/v1/usuarios/{admin_user['id']}")
    assert response.status_code == 200
    assert response.json()["activo"] is False
