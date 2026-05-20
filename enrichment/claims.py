"""Claim builder: assembles the response payload returned for a login."""
from __future__ import annotations

from typing import Any

from .models import UserClaim


def build_claims(claim: UserClaim) -> dict[str, Any]:
    """Merge persisted columns and the freeform ``claims`` JSON blob."""
    base: dict[str, Any] = {
        "login": claim.login,
        "cpf": claim.cpf or None,
        "rf": claim.rf or None,
        "matricula": claim.matricula or None,
        "nome": claim.nome or None,
        "email": claim.email or None,
        "source": claim.source or None,
        "tipo_usuario": claim.tipo_usuario or None,
    }
    extra = claim.claims or {}
    merged = {**base, **{k: v for k, v in extra.items() if k not in base or extra[k] is not None}}
    return merged
