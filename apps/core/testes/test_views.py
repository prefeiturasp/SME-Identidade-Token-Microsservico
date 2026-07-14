"""Testes da views do módulo core."""

from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class TestHealthCheckView:
    """Testes da view HealthCheckView."""

    def test_deve_retornar_aplicacao_saudavel(self) -> None:
        """Deve retornar o status de saúde da aplicação."""
        client = APIClient()
        client.credentials(
            HTTP_X_API_KEY=settings.API_KEY,
        )

        response = client.get(
            reverse("health-check"),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "status": "healthy",
        }
