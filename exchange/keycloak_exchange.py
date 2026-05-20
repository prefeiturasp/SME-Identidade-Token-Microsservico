"""Helper wrappers around the Keycloak Token Exchange endpoint (RFC 8693)."""
from __future__ import annotations

import logging
from typing import Any

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

GRANT_TOKEN_EXCHANGE = "urn:ietf:params:oauth:grant-type:token-exchange"


class KeycloakExchangeError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None,
                 payload: dict | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload or {}


def exchange(
    subject_token: str,
    *,
    audience: str,
    requested_token_type: str | None = None,
    requested_subject: str | None = None,
    scope: str | None = None,
    realm: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
) -> dict[str, Any]:
    server = settings.KEYCLOAK_SERVER_URL.rstrip("/")
    realm = realm or settings.KEYCLOAK_REALM
    url = f"{server}/realms/{realm}/protocol/openid-connect/token"

    data: dict[str, Any] = {
        "grant_type": GRANT_TOKEN_EXCHANGE,
        "subject_token": subject_token,
        "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "audience": audience,
        "client_id": client_id or settings.KEYCLOAK_CLIENT_ID,
    }
    secret = client_secret if client_secret is not None else settings.KEYCLOAK_CLIENT_SECRET
    if secret:
        data["client_secret"] = secret
    if requested_token_type:
        data["requested_token_type"] = requested_token_type
    if requested_subject:
        data["requested_subject"] = requested_subject
    if scope:
        data["scope"] = scope

    try:
        with httpx.Client(
            timeout=settings.KEYCLOAK_TIMEOUT,
            verify=settings.KEYCLOAK_VERIFY_SSL,
        ) as client:
            resp = client.post(
                url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
    except httpx.HTTPError as exc:
        raise KeycloakExchangeError(f"Falha de transporte: {exc}") from exc

    if resp.status_code >= 400:
        try:
            payload = resp.json()
        except ValueError:
            payload = {"raw": resp.text}
        raise KeycloakExchangeError(
            payload.get("error_description") or payload.get("error") or "exchange failed",
            status_code=resp.status_code,
            payload=payload,
        )
    return resp.json()
