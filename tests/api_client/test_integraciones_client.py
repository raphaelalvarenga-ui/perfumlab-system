from app.api_client import UserSession

from .conftest import json_response


def test_fragella_usage_usa_endpoint_y_jwt(make_api_client):
    requests = []
    session = UserSession(access_token="token-123", usuario_id=1, rol="ADMINISTRADOR")

    def handler(request):
        requests.append(request)
        assert request.method == "GET"
        assert request.url.path == "/api/v1/integraciones/fragella/usage"
        assert request.headers["authorization"] == "Bearer token-123"
        return json_response(
            200,
            {
                "plan": "free",
                "requests_made": 7,
                "requests_remaining": 93,
                "billing_period": None,
            },
        )

    client = make_api_client(handler, session=session)

    assert client.integraciones.fragella_usage() == {
        "plan": "free",
        "requests_made": 7,
        "requests_remaining": 93,
        "billing_period": None,
    }
    assert len(requests) == 1
