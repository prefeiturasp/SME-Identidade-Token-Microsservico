import pytest


@pytest.mark.django_db
def test_internal_token_required(unauth_client):
    resp = unauth_client.post("/api/v1/etl/push-batch", {}, format="json")
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_invalid_internal_token(unauth_client):
    unauth_client.credentials(HTTP_X_INTERNAL_TOKEN="wrong")
    resp = unauth_client.get("/api/v1/users/anything/claims")
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_internal_token_disabled(unauth_client, settings):
    settings.INTERNAL_TOKEN_REQUIRED = False
    resp = unauth_client.get("/api/v1/users/missing/claims")
    # bypassa autenticação, mas usuário não existe
    assert resp.status_code == 404
