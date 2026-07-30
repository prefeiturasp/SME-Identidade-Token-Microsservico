"""Testes dos utilitários de geração de um JWKS."""

import base64
from unittest.mock import MagicMock, patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from django.test import SimpleTestCase

from apps.tokens.libs.jwks import (
    _base64url_uint,
    _public_key_to_jwk,
    obter_jwks,
)

_PRIVATE_KEY = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

_PUBLIC_KEY_PEM = (
    _PRIVATE_KEY.public_key()
    .public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    .decode("utf-8")
)


class TestBase64UrlUint(SimpleTestCase):
    """Testa a conversão de inteiros para Base64URL."""

    def test_converte_inteiro_para_base64url(self) -> None:
        """Testa a conversão de um inteiro para Base64URL."""
        valor = 65537

        esperado = (
            base64.urlsafe_b64encode(
                valor.to_bytes(
                    (valor.bit_length() + 7) // 8,
                    "big",
                )
            )
            .rstrip(b"=")
            .decode("ascii")
        )

        self.assertEqual(
            _base64url_uint(valor),
            esperado,
        )

    def test_nao_inclui_padding(self) -> None:
        """Testa que o resultado não contém caracteres de padding."""
        resultado = _base64url_uint(65537)

        self.assertNotIn(
            "=",
            resultado,
        )


class TestPublicKeyToJwk(SimpleTestCase):
    """Testa a conversão de uma chave pública para JWK."""

    def test_converte_chave_publica_para_jwk(self) -> None:
        """Testa a conversão de uma chave pública RSA para JWK."""
        jwk = _public_key_to_jwk(
            public_key_pem=_PUBLIC_KEY_PEM,
            kid="token-v1",
            algoritmo="RS256",
        )

        self.assertEqual(
            jwk["kty"],
            "RSA",
        )
        self.assertEqual(
            jwk["kid"],
            "token-v1",
        )
        self.assertEqual(
            jwk["use"],
            "sig",
        )
        self.assertEqual(
            jwk["alg"],
            "RS256",
        )
        self.assertIn(
            "n",
            jwk,
        )
        self.assertIn(
            "e",
            jwk,
        )

    def test_lanca_erro_para_pem_invalido(self) -> None:
        """Testa que um PEM inválido gera erro."""
        with self.assertRaises(ValueError):
            _public_key_to_jwk(
                public_key_pem="chave-invalida",
                kid="token-v1",
                algoritmo="RS256",
            )


class TestObterJwks(SimpleTestCase):
    """Testa a geração do documento JWKS."""

    @patch("apps.tokens.libs.jwks.listar_chaves_publicas")
    def test_retorna_jwks_com_todas_as_chaves(
        self,
        mock_listar_chaves_publicas: MagicMock,
    ) -> None:
        """Testa a geração do documento JWKS."""
        mock_listar_chaves_publicas.return_value = [
            {
                "kid": "token-v1",
                "algoritmo": "RS256",
                "public_key": _PUBLIC_KEY_PEM,
            },
            {
                "kid": "token-v2",
                "algoritmo": "RS256",
                "public_key": _PUBLIC_KEY_PEM,
            },
        ]

        jwks = obter_jwks()

        self.assertIn(
            "keys",
            jwks,
        )
        self.assertEqual(
            len(jwks["keys"]),
            2,
        )

        primeira = jwks["keys"][0]

        self.assertEqual(
            primeira["kid"],
            "token-v1",
        )
        self.assertEqual(
            primeira["alg"],
            "RS256",
        )
        self.assertEqual(
            primeira["kty"],
            "RSA",
        )
        self.assertEqual(
            primeira["use"],
            "sig",
        )
        self.assertIn(
            "n",
            primeira,
        )
        self.assertIn(
            "e",
            primeira,
        )

    @patch("apps.tokens.libs.jwks.listar_chaves_publicas")
    def test_retorna_lista_vazia_quando_nao_existem_chaves(
        self,
        mock_listar_chaves_publicas: MagicMock,
    ) -> None:
        """Testa a geração do JWKS sem chaves públicas."""
        mock_listar_chaves_publicas.return_value = []

        self.assertEqual(
            obter_jwks(),
            {
                "keys": [],
            },
        )

    def test_lanca_erro_quando_chave_publica_nao_eh_rsa(
        self,
    ) -> None:
        """Testa que uma chave pública diferente de RSA gera TypeError."""
        private_key = ec.generate_private_key(
            ec.SECP256R1(),
        )

        public_key_pem = (
            private_key.public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode("utf-8")
        )

        with self.assertRaises(TypeError):
            _public_key_to_jwk(
                public_key_pem=public_key_pem,
                kid="token-v1",
                algoritmo="RS256",
            )
