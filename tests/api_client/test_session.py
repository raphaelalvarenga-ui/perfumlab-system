from app.api_client import UserSession


def test_user_session_role_helpers_and_clear():
    session = UserSession()
    session.set_token("token")
    session.set_user(
        {
            "id": 1,
            "nombre": "Admin",
            "username": "admin",
            "rol": "ADMINISTRADOR",
            "activo": True,
        }
    )

    assert session.is_authenticated
    assert session.is_admin
    assert not session.is_vendedor

    session.clear()

    assert not session.is_authenticated
    assert session.access_token is None
    assert session.rol == ""


def test_vendedor_role_helper():
    session = UserSession(rol="VENDEDOR")

    assert session.is_vendedor
    assert not session.is_admin
