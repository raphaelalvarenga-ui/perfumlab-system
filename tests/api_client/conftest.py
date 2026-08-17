from urllib.parse import parse_qs
import sys
from pathlib import Path

import httpx
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.api_client import ApiClient, UserSession


def json_response(status_code=200, payload=None):
    return httpx.Response(status_code, json=payload if payload is not None else {})


def form_data(request: httpx.Request):
    return {
        key: values[0]
        for key, values in parse_qs(request.content.decode()).items()
    }


@pytest.fixture
def make_api_client():
    clients = []

    def factory(handler, *, session=None):
        client = ApiClient(
            base_url="http://api.test",
            session=session or UserSession(),
            transport=httpx.MockTransport(handler),
        )
        clients.append(client)
        return client

    yield factory

    for client in clients:
        client.close()
