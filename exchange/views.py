"""Token Exchange endpoint (RFC 8693, via Keycloak)."""
from __future__ import annotations

import hashlib
import logging

from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .keycloak_exchange import KeycloakExchangeError, exchange
from .serializers import ExchangeRequestSerializer

logger = logging.getLogger(__name__)

CACHE_PREFIX = "token-ms:exchange:"
CACHE_SAFETY_MARGIN = 30


def _cache_key(subject_token: str, audience: str, scope: str) -> str:
    digest = hashlib.sha256(
        f"{subject_token}|{audience}|{scope}".encode()
    ).hexdigest()
    return f"{CACHE_PREFIX}{digest}"


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def token_exchange(request):
    """POST /api/v1/token/exchange — RFC 8693 token exchange via Keycloak."""
    serializer = ExchangeRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    v = serializer.validated_data

    scope = v.get("scope") or ""
    key = _cache_key(v["subject_token"], v["audience"], scope)
    cached = cache.get(key)
    if cached:
        return Response({**cached, "cached": True})

    try:
        payload = exchange(
            v["subject_token"],
            audience=v["audience"],
            requested_token_type=v.get("requested_token_type") or None,
            requested_subject=v.get("requested_subject") or None,
            scope=scope or None,
            client_id=v.get("client_id") or None,
            client_secret=v.get("client_secret") or None,
        )
    except KeycloakExchangeError as exc:
        return Response(
            {"detail": str(exc), "keycloak": exc.payload},
            status=exc.status_code or status.HTTP_502_BAD_GATEWAY,
        )

    expires_in = int(payload.get("expires_in", settings.EXCHANGE_TOKEN_TTL))
    ttl = max(min(expires_in, settings.EXCHANGE_TOKEN_TTL) - CACHE_SAFETY_MARGIN, 1)
    cached_payload = {
        "access_token": payload.get("access_token"),
        "token_type": payload.get("token_type", "Bearer"),
        "expires_in": expires_in,
        "scope": payload.get("scope"),
        "issued_token_type": payload.get("issued_token_type"),
    }
    cache.set(key, cached_payload, ttl)
    return Response({**cached_payload, "cached": False})
