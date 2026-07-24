"""Utilitários para validação de tokens JWT enriquecidos."""

from __future__ import annotations

from typing import Any

import jwt
from django.conf import settings

from apps.tokens.libs.jwt_chaves import (
    _obter_configuracao_str,
    listar_chaves_publicas,
)

_ISSUER = "sme-token-ms"


def obter_chave_publica_por_kid(kid: str) -> str:
    """Obtém a chave pública correspondente ao identificador informado.

    Args:
        kid: Identificador da chave pública.

    Returns:
        Chave pública em formato PEM.

    Raises:
        jwt.InvalidTokenError: Se nenhuma chave pública for encontrada para o
            identificador informado.
    """
    for chave in listar_chaves_publicas():
        if chave["kid"] == kid:
            return chave["public_key"]

    raise jwt.InvalidTokenError(
        "Chave pública não encontrada para o kid informado."
    )


def validar_token(token: str) -> dict[str, Any]:
    """Valida a assinatura e a expiração de um JWT enriquecido.

    Args:
        token: Token JWT a ser validado.

    Returns:
        Claims presentes no token.

    Raises:
        jwt.InvalidTokenError: Se o token não possuir um ``kid`` válido ou não
            for possível localizar a chave pública correspondente.
        jwt.PyJWTError: Se a validação da assinatura ou das claims falhar.
    """
    cabecalho = jwt.get_unverified_header(token)

    kid = cabecalho.get("kid")

    if not kid:
        raise jwt.InvalidTokenError("Token sem kid.")

    chave_publica = obter_chave_publica_por_kid(kid)

    algoritmo = _obter_configuracao_str(
        settings.JWT_ENRIQUECIDO_ALGORITMO,
        "JWT_ENRIQUECIDO_ALGORITMO",
    )

    claims = jwt.decode(
        token,
        chave_publica,
        algorithms=[algoritmo],
        issuer=_ISSUER,
    )

    if not isinstance(claims, dict):
        raise jwt.InvalidTokenError(
            "Claims do token possuem formato inválido."
        )

    return claims
