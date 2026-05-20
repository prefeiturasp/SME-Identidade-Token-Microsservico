"""Django settings for token-ms (SME-Identidade)."""
from __future__ import annotations

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "dev-insecure-change-in-production-token-ms-key"
)

DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "corsheaders",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "core.apps.CoreConfig",
    "enrichment.apps.EnrichmentConfig",
    "exchange.apps.ExchangeConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "token_ms.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    },
]

WSGI_APPLICATION = "token_ms.wsgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default="postgres://token:token@localhost:5436/token_db",
        conn_max_age=600,
        conn_health_checks=True,
    ),
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("CACHE_URL", "redis://localhost:6381/0"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "core.authentication.InternalTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S%z",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Token-MS API — SME Identidade",
    "DESCRIPTION": "Microsserviço de enriquecimento de claims e token exchange.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
}

_cors_raw = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
CORS_ALLOW_ALL_ORIGINS = DEBUG or "*" in _cors_raw
CORS_ALLOWED_ORIGINS = [] if CORS_ALLOW_ALL_ORIGINS else _cors_raw

# Internal auth: o token-ms só aceita tráfego interno (etl-ms, gateway-ms).
INTERNAL_TOKEN = os.environ.get("INTERNAL_TOKEN", "dev-internal-token")
INTERNAL_TOKEN_REQUIRED = (
    os.environ.get("INTERNAL_TOKEN_REQUIRED", "true").lower() == "true"
)
INTERNAL_TOKEN_HEADER = os.environ.get("INTERNAL_TOKEN_HEADER", "X-Internal-Token")

# Keycloak (usado pelo /token/exchange).
KEYCLOAK_SERVER_URL = os.environ.get("KEYCLOAK_SERVER_URL", "http://localhost:8080/")
KEYCLOAK_REALM = os.environ.get("KEYCLOAK_REALM", "sme-apps")
KEYCLOAK_CLIENT_ID = os.environ.get("KEYCLOAK_CLIENT_ID", "token-ms")
KEYCLOAK_CLIENT_SECRET = os.environ.get("KEYCLOAK_CLIENT_SECRET", "")
KEYCLOAK_VERIFY_SSL = os.environ.get("KEYCLOAK_VERIFY_SSL", "true").lower() == "true"
KEYCLOAK_TIMEOUT = int(os.environ.get("KEYCLOAK_TIMEOUT", "10"))

# TTLs.
CLAIMS_CACHE_TTL = int(os.environ.get("CLAIMS_CACHE_TTL", "300"))
EXCHANGE_TOKEN_TTL = int(os.environ.get("EXCHANGE_TOKEN_TTL", "300"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "INFO")},
}
