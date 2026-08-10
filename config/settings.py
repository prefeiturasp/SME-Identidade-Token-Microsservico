"""Configuração Django do SME-Identidade-Token-Microsservico."""

import os
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "dev-inseguro-apenas-desenvolvimento",
)
API_KEY = os.getenv("API_KEY", "dev-key-default")
API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [
    host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")
]
NIVEL_LOG = os.getenv("NIVEL_LOG", "INFO")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "apps.core",
    "apps.autenticacao",
    "apps.perfil",
    "apps.atributos_complementares",
    "apps.tokens",
    "apps.cache",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


def _url_para_bd(url: str | None) -> dict:
    """Converta URL PostgreSQL em dicionário de configuração Django."""
    if not url:
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}

    parsed = urllib.parse.urlparse(url)

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": parsed.path.lstrip("/"),
        "USER": parsed.username or "postgres",
        "PASSWORD": parsed.password or "postgres",
        "HOST": parsed.hostname or "localhost",
        "PORT": parsed.port or 5432,
        "CONN_MAX_AGE": 600,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }


DATABASES = {
    "default": _url_para_bd(os.getenv("IDENTIDADE_TOKEN_DB_URL")),
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.autenticacao.api.autenticacao.AutenticacaoApiKey",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "SME-Identidade-Token-Microsservico API",
    "DESCRIPTION": "API de controle do identidade-Token",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": API_KEY_HEADER,
            }
        }
    },
    "SECURITY": [{"ApiKeyAuth": []}],
}

JWT_ENRIQUECIDO_PRIVATE_KEY_PATH = os.getenv(
    "JWT_ENRIQUECIDO_PRIVATE_KEY_PATH"
)
JWT_ENRIQUECIDO_PUBLIC_KEY_PATH = os.getenv("JWT_ENRIQUECIDO_PUBLIC_KEY_PATH")
JWT_ENRIQUECIDO_KID = os.getenv("JWT_ENRIQUECIDO_KID")
JWT_ENRIQUECIDO_ALGORITMO = os.getenv("JWT_ENRIQUECIDO_ALGORITMO")
JWT_ENRIQUECIDO_TTL_SEGUNDOS = int(
    os.getenv("JWT_ENRIQUECIDO_TTL_SEGUNDOS", "28800")
)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("URL_KEYDB", "redis://keydb:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "TIMEOUT": int(os.getenv("KEYDB_DEFAULT_TIMEOUT", "300")),
    }
}

# ---------------------------------------------------------------------------
# Logging (python-json-logger — padrão Ateliê)
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.json.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
            "rename_fields": {
                "asctime": "timestamp",
                "levelname": "nivel",
                "name": "logger",
            },
            "json_ensure_ascii": False,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "loggers": {
        "identidade_token": {
            "handlers": ["console"],
            "level": NIVEL_LOG,
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": NIVEL_LOG,
    },
}
