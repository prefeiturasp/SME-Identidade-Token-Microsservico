"""Serviços responsáveis pela geração do Token Enriquecido."""

import logging
from typing import Any, cast
from uuid import UUID

from apps.cache import chaves
from apps.cache.services import CacheService
from apps.perfil.models import ProjecaoUsuario
from apps.tokens.token_enriquecido import compor_token_enriquecido

logger = logging.getLogger(__name__)


class TokenEnriquecidoService:
    """Serviço responsável por gerar o Token Enriquecido."""

    @staticmethod
    def gerar(
        usuario_id: UUID,
        conta_keycloak: dict,
        perfil: str | None,
    ) -> dict:
        """Gera um Token Enriquecido para um usuário.

        O Token Enriquecido é obtido do cache quando disponível.
        Caso contrário, a projeção do usuário é consultada, um novo
        token é gerado e armazenado em cache.

        Args:
            usuario_id: Identificador único do usuário.
            conta_keycloak: Dados da conta autenticada no Keycloak.
            perfil: Perfil selecionado para composição do token.

        Returns:
            Dados do Token Enriquecido contendo o JWT, a data de
            expiração e as permissões do usuário.
        """
        chave = chaves.token_enriquecido(usuario_id)

        resposta = cast(
            dict[str, Any] | None,
            CacheService.obter(chave),
        )

        if resposta is not None:
            logger.info(
                "Cache hit para o Token Enriquecido do usuário %s.",
                usuario_id,
            )
            return resposta

        logger.info(
            "Cache miss para o Token Enriquecido do usuário %s.",
            usuario_id,
        )

        projecao_usuario = TokenEnriquecidoService._obter_projecao_usuario(
            usuario_id,
        )

        token, expiracao, permissoes = compor_token_enriquecido(
            conta_keycloak=conta_keycloak,
            projecao_usuario=projecao_usuario,
            perfil=perfil,
        )

        logger.info(
            "Token Enriquecido gerado para o usuário %s.",
            usuario_id,
        )

        resposta = {
            "token": token,
            "data_expiracao": expiracao,
            "permissoes": permissoes,
        }

        CacheService.salvar(
            chave=chave,
            valor=resposta,
        )

        logger.info(
            "Token Enriquecido armazenado em cache para o usuário %s.",
            usuario_id,
        )

        return resposta

    @staticmethod
    def _obter_projecao_usuario(
        usuario_id: UUID,
    ) -> ProjecaoUsuario | None:
        """Obtém a projeção de um usuário.

        A projeção é carregada juntamente com seus perfis e módulos de
        permissão para evitar consultas adicionais durante a geração do
        Token Enriquecido.

        Args:
            usuario_id: Identificador único do usuário.

        Returns:
            Projeção do usuário ou ``None`` caso não exista.
        """
        return (
            ProjecaoUsuario.objects.prefetch_related(
                "perfis",
                "modulos_permissao",
            )
            .filter(usuario_id=usuario_id)
            .first()
        )

    @staticmethod
    def invalidar(usuario_id: UUID) -> None:
        """Invalida o Token Enriquecido em cache de um usuário.

        Remove do cache o Token Enriquecido associado ao usuário,
        garantindo que uma nova versão seja gerada na próxima
        solicitação.

        Args:
            usuario_id: Identificador único do usuário.
        """
        CacheService.invalidar(
            chaves.token_enriquecido(usuario_id),
        )

        logger.info(
            "Cache do Token Enriquecido invalidado para o usuário %s.",
            usuario_id,
        )
