"""Testes dos serializers do módulo atributos_complementares."""

from uuid import uuid4

from django.test import TestCase

from apps.atributos_complementares.api.serializers import (
    PushBatchSerializer,
)


class TestPushBatchSerializer(TestCase):
    """Testes do serializer PushBatchSerializer."""

    def setUp(self) -> None:
        """Cria um payload válido de referência."""
        self.payload = {
            "id_execucao": str(uuid4()),
            "usuarios": [
                {
                    "rf": "1234567",
                    "cpf": "12345678900",
                    "nome": "Usuário Teste",
                    "tipo_usuario": "servidor",
                    "cargo": "Professor",
                    "situacao": "ativo",
                    "fonte": "se1426",
                },
            ],
        }

    def test_deve_validar_payload_completo(self) -> None:
        """Deve validar um payload completo e correto."""
        serializer = PushBatchSerializer(data=self.payload)

        assert serializer.is_valid(), serializer.errors
        assert len(serializer.validated_data["usuarios"]) == 1

    def test_deve_validar_payload_sem_id_execucao(self) -> None:
        """Deve validar payload sem id_execucao (campo opcional)."""
        payload = self.payload.copy()
        payload.pop("id_execucao")

        serializer = PushBatchSerializer(data=payload)

        assert serializer.is_valid(), serializer.errors

    def test_deve_rejeitar_usuario_sem_identificador(self) -> None:
        """Deve rejeitar usuário sem rf, cpf ou matricula."""
        payload = self.payload.copy()
        payload["usuarios"] = [
            {
                "nome": "Usuário sem identificador",
                "situacao": "ativo",
            },
        ]

        serializer = PushBatchSerializer(data=payload)

        assert not serializer.is_valid()
        assert "usuarios" in serializer.errors

    def test_deve_aceitar_usuario_identificado_apenas_por_matricula(
        self,
    ) -> None:
        """Deve validar usuário identificado somente por matrícula."""
        payload = self.payload.copy()
        payload["usuarios"] = [
            {
                "matricula": "9998887",
                "nome": "Aluno Teste",
                "tipo_usuario": "aluno",
            },
        ]

        serializer = PushBatchSerializer(data=payload)

        assert serializer.is_valid(), serializer.errors

    def test_deve_aceitar_campos_opcionais_ausentes(self) -> None:
        """Deve validar payload só com o identificador obrigatório."""
        payload = {
            "usuarios": [{"rf": "1234567"}],
        }

        serializer = PushBatchSerializer(data=payload)

        assert serializer.is_valid(), serializer.errors

    def test_deve_rejeitar_lista_de_usuarios_vazia(self) -> None:
        """Deve validar payload com lista de usuários vazia."""
        payload = self.payload.copy()
        payload["usuarios"] = []

        serializer = PushBatchSerializer(data=payload)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["usuarios"] == []
