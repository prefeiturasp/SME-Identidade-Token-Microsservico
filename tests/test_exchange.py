from unittest.mock import MagicMock, patch

import httpx
import pytest

from exchange import keycloak_exchange


def _ctx(response):
    client = MagicMock()
    client.__enter__.return_value = client
    client.__exit__.return_value = False
    client.post.return_value = response
    return client


def _resp(status_code=200, body=None):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = body or {}
    resp.content = b"{}"
    resp.text = ""
    return resp


@pytest.mark.django_db
def test_token_exchange_success(api_client):
    payload = {
        "access_token": "NEW",
        "expires_in": 300,
        "token_type": "Bearer",
        "scope": "sistema-a",
        "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
    }
    with patch("exchange.views.exchange", return_value=payload) as mock_exc:
        resp = api_client.post(
            "/api/v1/token/exchange/",
            {"subject_token": "ABC", "audience": "sistema-a"},
            format="json",
        )
        resp2 = api_client.post(
            "/api/v1/token/exchange/",
            {"subject_token": "ABC", "audience": "sistema-a"},
            format="json",
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"] == "NEW"
    assert body["cached"] is False
    assert resp2.json()["cached"] is True
    assert mock_exc.call_count == 1


@pytest.mark.django_db
def test_token_exchange_error(api_client):
    err = keycloak_exchange.KeycloakExchangeError(
        "invalid_grant",
        status_code=400,
        payload={"error": "invalid_grant"},
    )
    with patch("exchange.views.exchange", side_effect=err):
        resp = api_client.post(
            "/api/v1/token/exchange/",
            {"subject_token": "X", "audience": "a"},
            format="json",
        )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_token_exchange_validation(api_client):
    resp = api_client.post("/api/v1/token/exchange/", {}, format="json")
    assert resp.status_code == 400


def test_keycloak_exchange_call_builds_payload():
    captured = {}

    def _post(url, data, headers):
        captured["url"] = url
        captured["data"] = data
        return _resp(200, {"access_token": "X", "expires_in": 300})

    with patch("exchange.keycloak_exchange.httpx.Client") as MockClient:
        client = _ctx(_resp(200, {"access_token": "X", "expires_in": 300}))
        client.post.side_effect = _post
        MockClient.return_value = client
        result = keycloak_exchange.exchange(
            "subj",
            audience="aud",
            requested_token_type="urn:type",
            requested_subject="user-1",
            scope="s",
            client_id="c",
            client_secret="cs",
        )
    assert result["access_token"] == "X"
    assert captured["data"]["audience"] == "aud"
    assert captured["data"]["requested_subject"] == "user-1"
    assert captured["data"]["client_secret"] == "cs"
    assert captured["data"]["scope"] == "s"
    assert captured["data"]["requested_token_type"] == "urn:type"


def test_keycloak_exchange_transport_error():
    with patch("exchange.keycloak_exchange.httpx.Client") as MockClient:
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        client.post.side_effect = httpx.ConnectError("nope")
        MockClient.return_value = client
        with pytest.raises(keycloak_exchange.KeycloakExchangeError):
            keycloak_exchange.exchange("subj", audience="aud")


def test_keycloak_exchange_error_response():
    with patch("exchange.keycloak_exchange.httpx.Client") as MockClient:
        MockClient.return_value = _ctx(
            _resp(400, {"error": "x", "error_description": "boom"})
        )
        with pytest.raises(keycloak_exchange.KeycloakExchangeError) as exc:
            keycloak_exchange.exchange("subj", audience="aud")
    assert exc.value.status_code == 400
