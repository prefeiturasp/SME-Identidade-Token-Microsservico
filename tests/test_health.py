import pytest


@pytest.mark.django_db
def test_liveness(unauth_client):
    resp = unauth_client.get("/api/health/")
    assert resp.status_code == 200
    assert resp.json()["service"] == "token-ms"


@pytest.mark.django_db
def test_readiness(unauth_client):
    resp = unauth_client.get("/api/health/ready/")
    assert resp.status_code == 200
