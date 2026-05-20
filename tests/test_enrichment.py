import uuid

import pytest

from enrichment.models import ETLBatchLog, UserClaim


@pytest.fixture
def sample_batch():
    return {
        "execution_id": str(uuid.uuid4()),
        "users": [
            {
                "login": "12345",
                "cpf": "11122233344",
                "rf": "12345",
                "nome": "Maria",
                "email": "maria@sme.gov.br",
                "source": "se1426",
                "tipo_usuario": "servidor",
                "claims": {"perfis": ["uuid-1"], "permissoes_por_perfil": {"uuid-1": ["READ"]}},
            },
            {
                "rf": "9999",
                "nome": "Sem CPF",
                "source": "eol_db",
                "tipo_usuario": "servidor",
                "claims": {},
            },
        ],
    }


@pytest.mark.django_db
def test_push_batch_creates_users(api_client, sample_batch):
    resp = api_client.post("/api/v1/etl/push-batch", sample_batch, format="json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["created"] == 2
    assert body["updated"] == 0
    assert body["failed"] == 0
    assert UserClaim.objects.count() == 2
    assert ETLBatchLog.objects.count() == 1


@pytest.mark.django_db
def test_push_batch_updates_existing(api_client, sample_batch):
    api_client.post("/api/v1/etl/push-batch", sample_batch, format="json")
    sample_batch["users"][0]["nome"] = "Maria Atualizada"
    resp = api_client.post("/api/v1/etl/push-batch", sample_batch, format="json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["updated"] == 2
    assert UserClaim.objects.get(login="12345").nome == "Maria Atualizada"


@pytest.mark.django_db
def test_push_batch_validation_error(api_client):
    resp = api_client.post(
        "/api/v1/etl/push-batch",
        {"users": [{"nome": "Sem identificador"}]},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_user_claims_endpoint(api_client, sample_batch):
    api_client.post("/api/v1/etl/push-batch", sample_batch, format="json")
    resp = api_client.get("/api/v1/users/12345/claims")
    assert resp.status_code == 200
    body = resp.json()
    assert body["cpf"] == "11122233344"
    assert body["perfis"] == ["uuid-1"]
    assert body["_cached"] is False
    # Second call hits cache.
    resp2 = api_client.get("/api/v1/users/12345/claims")
    assert resp2.status_code == 200
    assert resp2.json()["_cached"] is True


@pytest.mark.django_db
def test_user_claims_not_found(api_client):
    resp = api_client.get("/api/v1/users/0000/claims")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_admin_claims_listing(api_client, sample_batch):
    api_client.post("/api/v1/etl/push-batch", sample_batch, format="json")
    resp = api_client.get("/api/v1/admin/claims/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2


@pytest.mark.django_db
def test_admin_claims_invalidate(api_client, sample_batch):
    api_client.post("/api/v1/etl/push-batch", sample_batch, format="json")
    api_client.get("/api/v1/users/12345/claims")  # popula cache
    resp = api_client.post("/api/v1/admin/claims/12345/invalidate-cache/")
    assert resp.status_code == 200
    second = api_client.get("/api/v1/users/12345/claims")
    assert second.json()["_cached"] is False


@pytest.mark.django_db
def test_admin_etl_logs(api_client, sample_batch):
    api_client.post("/api/v1/etl/push-batch", sample_batch, format="json")
    resp = api_client.get("/api/v1/admin/etl-logs/")
    assert resp.status_code == 200
    assert resp.json()["count"] == 1
