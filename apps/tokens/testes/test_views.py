"""Testes das views do módulo tokens."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import jwt
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


def criar_client() -> APIClient:
    """Cria um cliente autenticado para os testes."""
    client = APIClient()
    client.credentials(
        HTTP_X_API_KEY=settings.API_KEY,
    )

    return client


class TestJWKSView:
    """Testes da view JWKSView."""

    @patch("apps.tokens.api.views.obter_jwks")
    def test_deve_retornar_documento_jwks(
        self,
        mock_obter_jwks: MagicMock,
    ) -> None:
        """Deve retornar o JWKS."""
        mock_obter_jwks.return_value = {
            "keys": [
                {
                    "kid": "token-v1",
                }
            ]
        }

        client = criar_client()

        response = client.get(
            reverse("jwks"),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "keys": [
                {
                    "kid": "token-v1",
                }
            ]
        }

        mock_obter_jwks.assert_called_once()


class TestTokenEnriquecidoView:
    """Testes da view TokenEnriquecidoView."""

    @patch(
        "apps.tokens.api.views.compor_token_enriquecido",
    )
    @patch(
        "apps.tokens.api.views.ProjecaoUsuario.objects",
    )
    def test_deve_gerar_token_enriquecido(
        self,
        mock_objects: MagicMock,
        mock_compor_token: MagicMock,
    ) -> None:
        """Deve gerar um token enriquecido."""
        usuario_id = uuid4()

        projecao_usuario = MagicMock()

        (
            mock_objects.prefetch_related.return_value.filter.return_value.first.return_value
        ) = projecao_usuario

        expiracao = datetime.now(UTC)

        permissoes = [
            {
                "sistema_id": 1,
                "sistema_nome": "CoreSSO",
                "modulo_id": 3,
                "modulo_nome": "Usuários",
                "consultar": True,
                "inserir": False,
                "alterar": False,
                "excluir": False,
            }
        ]

        mock_compor_token.return_value = (
            "token-jwt",
            expiracao,
            permissoes,
        )

        payload = {
            "kc_user_id": "123",
            "username": "usuario",
            "perfil": "professor",
        }

        client = criar_client()

        response = client.post(
            reverse(
                "token-enriquecido",
                kwargs={
                    "usuario_id": usuario_id,
                },
            ),
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["token"] == "token-jwt"
        assert response.json()["data_expiracao"] is not None
        assert response.json()["permissoes"] == permissoes

        mock_compor_token.assert_called_once_with(
            conta_keycloak=payload,
            projecao_usuario=projecao_usuario,
            perfil="professor",
        )

    @patch(
        "apps.tokens.api.views.compor_token_enriquecido",
    )
    @patch(
        "apps.tokens.api.views.ProjecaoUsuario.objects",
    )
    def test_deve_gerar_token_sem_projecao_usuario(
        self,
        mock_objects: MagicMock,
        mock_compor_token: MagicMock,
    ) -> None:
        """Deve gerar token quando usuário não possui projeção."""
        usuario_id = uuid4()

        (
            mock_objects.prefetch_related.return_value.filter.return_value.first.return_value
        ) = None

        mock_compor_token.return_value = (
            "token-jwt",
            datetime.now(UTC),
            [],
        )

        payload = {
            "kc_user_id": "123",
            "username": "usuario",
        }

        client = criar_client()

        response = client.post(
            reverse(
                "token-enriquecido",
                kwargs={
                    "usuario_id": usuario_id,
                },
            ),
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["token"] == "token-jwt"
        assert response.json()["permissoes"] == []
        assert response.json()["data_expiracao"] is not None

        mock_compor_token.assert_called_once_with(
            conta_keycloak=payload,
            projecao_usuario=None,
            perfil=None,
        )


class TestValidarTokenView:
    """Testes da view ValidarTokenView."""

    @patch(
        "apps.tokens.api.views.validar_token",
    )
    def test_deve_validar_token_com_sucesso(
        self,
        mock_validar_token: MagicMock,
    ) -> None:
        """Deve validar um token JWT válido."""
        claims = {
            "sub": "usuario",
            "iss": "sme-token-ms",
        }

        mock_validar_token.return_value = claims

        client = criar_client()

        response = client.post(
            reverse("token-validar"),
            {
                "token": "token-valido",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "valido": True,
            "expirado": False,
            "claims": claims,
        }

        mock_validar_token.assert_called_once_with(
            "token-valido",
        )

    @patch(
        "apps.tokens.api.views.validar_token",
    )
    def test_deve_retornar_token_expirado(
        self,
        mock_validar_token: MagicMock,
    ) -> None:
        """Deve retornar erro quando token estiver expirado."""
        mock_validar_token.side_effect = jwt.ExpiredSignatureError()

        client = criar_client()

        response = client.post(
            reverse("token-validar"),
            {
                "token": "token-expirado",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            "valido": False,
            "expirado": True,
        }

    @patch(
        "apps.tokens.api.views.validar_token",
    )
    def test_deve_retornar_token_invalido(
        self,
        mock_validar_token: MagicMock,
    ) -> None:
        """Deve retornar erro quando token for inválido."""
        mock_validar_token.side_effect = jwt.InvalidTokenError()

        client = criar_client()

        response = client.post(
            reverse("token-validar"),
            {
                "token": "token-invalido",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            "valido": False,
            "expirado": False,
        }

    def test_deve_retornar_erro_com_payload_invalido(
        self,
    ) -> None:
        """Deve retornar erro quando payload não possuir token."""
        client = criar_client()

        response = client.post(
            reverse("token-validar"),
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "token" in response.json()
