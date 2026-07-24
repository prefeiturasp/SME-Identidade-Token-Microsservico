"""Utilitários para geração de um JSON Web Key Set (JWKS)."""

from __future__ import annotations

import base64
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from apps.tokens.libs.jwt_chaves import listar_chaves_publicas


def _base64url_uint(value: int) -> str:
    """Transforma um inteiro para Base64URL sem preenchimento.

    Args:
        value: Valor inteiro a ser convertido.

    Returns:
        Valor codificado em Base64URL sem caracteres de padding.
    """
    length = (value.bit_length() + 7) // 8

    return (
        base64.urlsafe_b64encode(value.to_bytes(length, "big"))
        .rstrip(b"=")
        .decode("ascii")
    )


def _public_key_to_jwk(
    public_key_pem: str,
    kid: str,
    algoritmo: str,
) -> dict[str, Any]:
    """Transforma uma chave pública PEM para o formato JWK.

    Args:
        public_key_pem: Chave pública em formato PEM.
        kid: Identificador único da chave.
        algoritmo: Algoritmo utilizado para assinatura.

    Returns:
        Representação da chave pública no formato JWK.

    Raises:
        TypeError: Caso a chave pública não seja do tipo RSA.
    """
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode("utf-8")
    )

    if not isinstance(public_key, RSAPublicKey):
        raise TypeError("A chave pública deve ser RSA.")

    numbers = public_key.public_numbers()

    return {
        "kty": "RSA",
        "kid": kid,
        "use": "sig",
        "alg": algoritmo,
        "n": _base64url_uint(numbers.n),
        "e": _base64url_uint(numbers.e),
    }


def obter_jwks() -> dict[str, list[dict[str, Any]]]:
    """Obtém o conjunto de chaves públicas no formato JWKS.

    Returns:
        Dicionário contendo a propriedade ``keys`` com todas as chaves
        públicas disponíveis para validação de JWTs.
    """
    return {
        "keys": [
            _public_key_to_jwk(
                public_key_pem=chave["public_key"],
                kid=chave["kid"],
                algoritmo=chave["algoritmo"],
            )
            for chave in listar_chaves_publicas()
        ]
    }
