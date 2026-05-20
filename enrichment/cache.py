"""Cache helpers around the user-claim store."""
from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.cache import cache

_PREFIX = "token-ms:claims:"


def _key(login: str) -> str:
    return f"{_PREFIX}{login.lower()}"


def get(login: str) -> dict[str, Any] | None:
    return cache.get(_key(login))


def set(login: str, payload: dict[str, Any]) -> None:  # noqa: A001
    cache.set(_key(login), payload, settings.CLAIMS_CACHE_TTL)


def invalidate(login: str) -> None:
    cache.delete(_key(login))
