"""Testes dos utilitários de validação de JWT."""

from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import MagicMock, patch

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import SimpleTestCase, override_settings

from apps.tokens.libs.jwt_validacao import (
    obter_chave_publica_por_kid,
    validar_token,
)

_PRIVATE_KEY = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

_PRIVATE_KEY_PEM = _PRIVATE_KEY.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

_PUBLIC_KEY_PEM = (
    _PRIVATE_KEY.public_key()
    .public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    .decode("utf-8")
)


@override_settings(
    JWT_ENRIQUECIDO_ALGORITMO="RS256",
)
class TestObterChavePublicaPorKid(SimpleTestCase):
    """Testa a obtenção de chaves públicas."""

    @patch("apps.tokens.libs.jwt_validacao.listar_chaves_publicas")
    def test_retorna_chave_publica(
        self,
        mock_listar_chaves_publicas: MagicMock,
    ) -> None:
        """Testa a obtenção da chave pública pelo identificador."""
        mock_listar_chaves_publicas.return_value = [
            {
                "kid": "token-v1",
                "algoritmo": "RS256",
                "public_key": _PUBLIC_KEY_PEM,
            }
        ]

        chave = obter_chave_publica_por_kid("token-v1")

        self.assertEqual(chave, _PUBLIC_KEY_PEM)

    @patch("apps.tokens.libs.jwt_validacao.listar_chaves_publicas")
    def test_lanca_erro_quando_kid_nao_encontrado(
        self,
        mock_listar_chaves_publicas: MagicMock,
    ) -> None:
        """Testa que um kid inexistente gera erro."""
        mock_listar_chaves_publicas.return_value = []

        with self.assertRaises(jwt.InvalidTokenError):
            obter_chave_publica_por_kid("token-v1")


@override_settings(
    JWT_ENRIQUECIDO_ALGORITMO="RS256",
)
class TestValidarToken(SimpleTestCase):
    """Testa a validação de tokens JWT."""

    def _gerar_token(
        self,
        *,
        kid: str = "token-v1",
        issuer: str = "sme-token-ms",
        private_key: bytes = _PRIVATE_KEY_PEM,
    ) -> str:
        """Gera um token JWT válido para os testes."""
        agora = datetime.now(UTC)

        claims = {
            "iss": issuer,
            "sub": "usuario",
            "iat": int(agora.timestamp()),
            "exp": int((agora + timedelta(minutes=5)).timestamp()),
        }

        token = jwt.encode(
            claims,
            private_key,
            algorithm="RS256",
            headers={"kid": kid},
        )

        return cast(str, token)

    @patch("apps.tokens.libs.jwt_validacao.obter_chave_publica_por_kid")
    def test_valida_token(
        self,
        mock_obter_chave_publica: MagicMock,
    ) -> None:
        """Testa a validação de um token válido."""
        mock_obter_chave_publica.return_value = _PUBLIC_KEY_PEM

        token = self._gerar_token()

        claims = validar_token(token)

        self.assertEqual(claims["sub"], "usuario")
        self.assertEqual(claims["iss"], "sme-token-ms")

        mock_obter_chave_publica.assert_called_once_with("token-v1")

    def test_lanca_erro_quando_token_nao_possui_kid(
        self,
    ) -> None:
        """Testa que um token sem kid gera erro."""
        agora = datetime.now(UTC)

        token = jwt.encode(
            {
                "iss": "sme-token-ms",
                "sub": "usuario",
                "iat": int(agora.timestamp()),
                "exp": int((agora + timedelta(minutes=5)).timestamp()),
            },
            _PRIVATE_KEY_PEM,
            algorithm="RS256",
        )

        with self.assertRaises(jwt.InvalidTokenError):
            validar_token(token)

    @patch("apps.tokens.libs.jwt_validacao.obter_chave_publica_por_kid")
    def test_lanca_erro_quando_kid_nao_encontrado(
        self,
        mock_obter_chave_publica: MagicMock,
    ) -> None:
        """Testa que um kid inexistente gera erro."""
        mock_obter_chave_publica.side_effect = jwt.InvalidTokenError(
            "Chave não encontrada."
        )

        token = self._gerar_token()

        with self.assertRaises(jwt.InvalidTokenError):
            validar_token(token)

    @patch("apps.tokens.libs.jwt_validacao.obter_chave_publica_por_kid")
    def test_lanca_erro_quando_assinatura_eh_invalida(
        self,
        mock_obter_chave_publica: MagicMock,
    ) -> None:
        """Testa que uma assinatura inválida gera erro."""
        outra_chave = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        outra_publica = (
            outra_chave.public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode("utf-8")
        )

        mock_obter_chave_publica.return_value = outra_publica

        token = self._gerar_token()

        with self.assertRaises(jwt.InvalidSignatureError):
            validar_token(token)

    @patch("apps.tokens.libs.jwt_validacao.obter_chave_publica_por_kid")
    def test_lanca_erro_quando_issuer_eh_invalido(
        self,
        mock_obter_chave_publica: MagicMock,
    ) -> None:
        """Testa que um issuer inválido gera erro."""
        mock_obter_chave_publica.return_value = _PUBLIC_KEY_PEM

        token = self._gerar_token(
            issuer="issuer-invalido",
        )

        with self.assertRaises(jwt.InvalidIssuerError):
            validar_token(token)

    @patch("apps.tokens.libs.jwt_validacao.jwt.decode")
    @patch("apps.tokens.libs.jwt_validacao.obter_chave_publica_por_kid")
    def test_lanca_erro_quando_claims_nao_sao_um_dict(
        self,
        mock_obter_chave_publica: MagicMock,
        mock_decode: MagicMock,
    ) -> None:
        """Testa que claims em formato inválido geram erro."""
        mock_obter_chave_publica.return_value = _PUBLIC_KEY_PEM

        mock_decode.return_value = ["claim-invalida"]

        token = self._gerar_token()

        with self.assertRaises(jwt.InvalidTokenError):
            validar_token(token)

        mock_decode.assert_called_once()
