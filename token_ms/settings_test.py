from token_ms.settings import *  # noqa: F401,F403

DEBUG = False
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "token-ms-tests",
    }
}
INTERNAL_TOKEN = "test-internal-token"
INTERNAL_TOKEN_REQUIRED = True
KEYCLOAK_VERIFY_SSL = False
CLAIMS_CACHE_TTL = 60
EXCHANGE_TOKEN_TTL = 60
