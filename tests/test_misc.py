"""Tests for the claim builder, cache helpers and authentication user class."""
import pytest

from core.authentication import InternalTokenUser
from enrichment import cache as claim_cache
from enrichment.claims import build_claims
from enrichment.models import UserClaim


def test_internal_token_user_repr():
    user = InternalTokenUser("svc")
    assert user.is_authenticated is True
    assert user.is_anonymous is False
    assert "svc" in str(user)


@pytest.mark.django_db
def test_build_claims_merges_blobs():
    claim = UserClaim.objects.create(
        login="abc",
        cpf="111",
        nome="Joana",
        claims={"perfis": [1], "rf": None},
    )
    payload = build_claims(claim)
    assert payload["cpf"] == "111"
    assert payload["nome"] == "Joana"
    assert payload["perfis"] == [1]


@pytest.mark.django_db
def test_cache_set_get_invalidate():
    claim_cache.set("login-x", {"k": 1})
    assert claim_cache.get("login-x") == {"k": 1}
    claim_cache.invalidate("login-x")
    assert claim_cache.get("login-x") is None
