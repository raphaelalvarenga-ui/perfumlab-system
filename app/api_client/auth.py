from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.api_client.client import ApiClient
    from app.api_client.session import UserSession


class AuthClient:
    def __init__(self, api: ApiClient):
        self.api = api

    def login(self, username: str, password: str) -> UserSession:
        data = self.api.request(
            "POST",
            "/api/v1/auth/login",
            data={"username": username, "password": password},
            auth_required=False,
        )
        self.api.session.set_token(str(data["access_token"]))
        user = self.me()
        if not user.get("activo", False):
            self.api.session.clear()
            from app.api_client.exceptions import ApiAuthenticationError

            raise ApiAuthenticationError("El usuario esta inactivo.", status_code=401)
        self.api.session.set_user(user)
        return self.api.session

    def me(self) -> dict:
        return self.api.request("GET", "/api/v1/auth/me")

    def logout(self) -> None:
        self.api.session.clear()
