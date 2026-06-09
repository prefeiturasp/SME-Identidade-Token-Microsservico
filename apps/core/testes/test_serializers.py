"""Testes dos serializers do módulo core."""

import pytest

from apps.core.api.serializers import HealthStatusSerializer


class TestHealthStatusSerializer:
    """Testes do serializer HealthStatusSerializer."""

    @pytest.mark.parametrize(
        "status",
        ["healthy", "degraded", "unhealthy"],
    )
    def test_deve_validar_status_permitidos(self, status):
        """Deve validar corretamente os status permitidos."""
        serializer = HealthStatusSerializer(
            data={"status": status},
        )

        assert serializer.is_valid()
        assert serializer.validated_data["status"] == status

    def test_deve_rejeitar_status_invalido(self):
        """Deve retornar erro quando o status for inválido."""
        serializer = HealthStatusSerializer(
            data={"status": "offline"},
        )

        assert not serializer.is_valid()
        assert "status" in serializer.errors

    def test_deve_exigir_campo_status(self):
        """Deve retornar erro quando o campo status não for enviado."""
        serializer = HealthStatusSerializer(data={})

        assert not serializer.is_valid()
        assert "status" in serializer.errors

    def test_deve_serializar_dados_corretamente(self):
        """Deve serializar os dados corretamente."""
        serializer = HealthStatusSerializer(
            instance={"status": "healthy"},
        )

        assert serializer.data == {
            "status": "healthy",
        }
