"""Compõe e assina o JWT enriquecido do Token-MS."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from django.conf import settings

from apps.perfil.models import ProjecaoUsuario
from apps.tokens.libs.jwt_chaves import obter_chave_privada

_ISSUER = "sme-token-ms"


def compor_token_enriquecido(
    conta_keycloak: dict[str, Any],
    projecao_usuario: ProjecaoUsuario | None,
    perfil: str | None = None,
) -> tuple[str, datetime, list[dict[str, Any]]]:
    """Compõe e assina um JWT enriquecido.

    Args:
        conta_keycloak: Dados da conta retornados pelo Keycloak.
        projecao_usuario: Projeção do usuário utilizada para enriquecer token.
        perfil: Identificador do perfil selecionado.

    Returns:
        Uma tupla contendo o JWT assinado, sua data de expiração
        e as permissões associadas ao usuário.
    """
    agora = datetime.now(UTC)
    ttl = settings.JWT_ENRIQUECIDO_TTL_SEGUNDOS
    expiracao = agora + timedelta(seconds=ttl)

    claims: dict[str, Any] = {
        "iss": _ISSUER,
        "iat": int(agora.timestamp()),
        "exp": int(expiracao.timestamp()),
        "sub": str(conta_keycloak.get("kc_user_id", "")),
        "preferred_username": conta_keycloak.get("username", ""),
        "email": conta_keycloak.get("email"),
        "rf": conta_keycloak.get("rf"),
        "cpf": conta_keycloak.get("cpf"),
        "perfis": [],
        "permissoes": [],
    }

    if projecao_usuario:
        claims.update(
            {
                "rf": projecao_usuario.rf,
                "nome": projecao_usuario.nome,
                "cpf": projecao_usuario.cpf,
                "situacao": projecao_usuario.situacao,
                "dre_codigo": projecao_usuario.dre_codigo,
                "contrato_externo": projecao_usuario.contrato_externo,
                "perfis": [
                    {
                        "id": str(perfil_usuario.id),
                        "nome": perfil_usuario.nome,
                        "ativo": perfil_usuario.ativo,
                    }
                    for perfil_usuario in projecao_usuario.perfis.all()
                ],
                "permissoes": [
                    {
                        "sistema_id": permissao.sistema_id,
                        "sistema_nome": permissao.sistema_nome,
                        "modulo_id": permissao.modulo_id,
                        "modulo_nome": permissao.modulo_nome,
                        "consultar": permissao.consultar,
                        "inserir": permissao.inserir,
                        "alterar": permissao.alterar,
                        "excluir": permissao.excluir,
                    }
                    for permissao in (projecao_usuario.modulos_permissao.all())
                ],
            }
        )

    if perfil:
        claims["perfilSelecionado"] = perfil

    headers = {
        "kid": settings.JWT_ENRIQUECIDO_KID,
    }

    permissoes: list[dict[str, Any]] = claims["permissoes"]

    token = jwt.encode(
        claims,
        obter_chave_privada(),
        algorithm=settings.JWT_ENRIQUECIDO_ALGORITMO,
        headers=headers,
    )

    return token, expiracao, permissoes
