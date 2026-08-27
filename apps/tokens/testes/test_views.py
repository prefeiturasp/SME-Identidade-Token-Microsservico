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

    @patch("apps.tokens.api.views.TokenEnriquecidoService.gerar")
    def test_deve_gerar_token_enriquecido(
        self,
        mock_gerar: MagicMock,
    ) -> None:
        """Deve gerar um Token Enriquecido."""
        usuario_id = uuid4()

        resposta = {
            "token": "token-jwt",
            "data_expiracao": datetime.now(UTC),
            "permissoes": [],
        }

        mock_gerar.return_value = resposta

        kc_user_id = uuid4()

        payload = {
            "kc_user_id": str(kc_user_id),
            "username": "usuario",
            "nome": "Usuário Teste",
            "email": "usuario@sme.prefeitura.sp.gov.br",
            "ativo": True,
            "cpf": "12345678900",
            "rf": "123456",
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
        assert response.json() == {
            "token": "token-jwt",
            "data_expiracao": response.json()["data_expiracao"],
            "permissoes": [],
        }

        mock_gerar.assert_called_once_with(
            usuario_id=usuario_id,
            conta_keycloak={
                "kc_user_id": kc_user_id,
                "username": payload["username"],
                "nome": payload["nome"],
                "email": payload["email"],
                "ativo": payload["ativo"],
                "cpf": payload["cpf"],
                "rf": payload["rf"],
                "perfil": payload["perfil"],
            },
            perfil="professor",
        )

    @patch("apps.tokens.api.views.TokenEnriquecidoService.gerar")
    def test_deve_gerar_token_sem_perfil_cpf_e_rf_no_payload(
        self,
        mock_gerar: MagicMock,
    ) -> None:
        """Reproduz o payload real enviado pelo Gateway no login.

        O Gateway chama este endpoint logo após autenticar no
        Keycloak, sem que o usuário tenha escolhido um perfil ainda
        — e ``cpf``/``rf`` podem não existir como atributo do
        usuário no Keycloak. Nenhum dos três deve ser obrigatório.
        """
        usuario_id = uuid4()
        kc_user_id = uuid4()

        mock_gerar.return_value = {
            "token": "token-jwt",
            "data_expiracao": datetime.now(UTC),
            "permissoes": [],
        }

        payload = {
            "kc_user_id": str(kc_user_id),
            "username": "usuario",
            "nome": "Usuário Teste",
            "email": "usuario@sme.prefeitura.sp.gov.br",
            "ativo": True,
        }

        client = criar_client()

        response = client.post(
            reverse(
                "token-enriquecido",
                kwargs={"usuario_id": usuario_id},
            ),
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        mock_gerar.assert_called_once_with(
            usuario_id=usuario_id,
            conta_keycloak={
                "kc_user_id": kc_user_id,
                "username": payload["username"],
                "nome": payload["nome"],
                "email": payload["email"],
                "ativo": payload["ativo"],
            },
            perfil=None,
        )

    @patch("apps.tokens.api.views.TokenEnriquecidoService.gerar")
    def test_deve_gerar_token_com_perfil_cpf_e_rf_nulos(
        self,
        mock_gerar: MagicMock,
    ) -> None:
        """Mesmo cenário do Gateway, mas com os campos enviados como null."""
        usuario_id = uuid4()
        kc_user_id = uuid4()

        mock_gerar.return_value = {
            "token": "token-jwt",
            "data_expiracao": datetime.now(UTC),
            "permissoes": [],
        }

        payload = {
            "kc_user_id": str(kc_user_id),
            "username": "usuario",
            "nome": "Usuário Teste",
            "email": "usuario@sme.prefeitura.sp.gov.br",
            "ativo": True,
            "cpf": None,
            "rf": None,
            "perfil": None,
        }

        client = criar_client()

        response = client.post(
            reverse(
                "token-enriquecido",
                kwargs={"usuario_id": usuario_id},
            ),
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        mock_gerar.assert_called_once_with(
            usuario_id=usuario_id,
            conta_keycloak={
                "kc_user_id": kc_user_id,
                "username": payload["username"],
                "nome": payload["nome"],
                "email": payload["email"],
                "ativo": payload["ativo"],
                "cpf": None,
                "rf": None,
                "perfil": None,
            },
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
