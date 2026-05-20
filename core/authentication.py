"""Internal-token authentication for token-ms.

The token-ms is *not* meant to be exposed to the public internet. Every
non-health request must carry the ``X-Internal-Token`` header (configurable
via ``INTERNAL_TOKEN_HEADER``) and match ``INTERNAL_TOKEN`` from settings.
"""
from __future__ import annotations

from django.conf import settings
from rest_framework import authentication, exceptions


class InternalTokenUser:
    """Anonymous-but-authenticated principal used after a successful check."""

    is_authenticated = True
    is_anonymous = False

    def __init__(self, source: str = "internal") -> None:
        self.source = source

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"InternalTokenUser({self.source})"


class InternalTokenAuthentication(authentication.BaseAuthentication):
    """Validates the shared ``X-Internal-Token`` header."""

    def authenticate(self, request):
        if not getattr(settings, "INTERNAL_TOKEN_REQUIRED", True):
            return (InternalTokenUser("disabled"), None)

        header = getattr(settings, "INTERNAL_TOKEN_HEADER", "X-Internal-Token")
        wire_name = "HTTP_" + header.upper().replace("-", "_")
        provided = request.META.get(wire_name)
        if not provided:
            raise exceptions.AuthenticationFailed("internal token missing")
        if provided != settings.INTERNAL_TOKEN:
            raise exceptions.AuthenticationFailed("internal token invalid")
        return (InternalTokenUser(), None)
