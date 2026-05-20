import pytest
from django.conf import settings
from rest_framework.test import APIClient


@pytest.fixture
def auth_headers():
    return {f"HTTP_{settings.INTERNAL_TOKEN_HEADER.replace('-', '_').upper()}": settings.INTERNAL_TOKEN}


@pytest.fixture
def api_client(auth_headers):
    client = APIClient()
    # Sticky default headers
    client.credentials(**auth_headers)
    return client


@pytest.fixture
def unauth_client():
    return APIClient()
