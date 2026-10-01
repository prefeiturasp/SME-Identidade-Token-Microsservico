"""Serviços responsáveis pela geração do Token Enriquecido."""

import logging
from typing import Any, cast
from uuid import UUID

from django.db.models import Prefetch

from apps.cache import chaves
from apps.cache.services import CacheService
from apps.perfil.models import ModuloPermissaoUsuario, ProjecaoUsuario
from apps.tokens.token_enriquecido import compor_token_enriquecido

logger = logging.getLogger(__name__)


class TokenEnriquecidoService:
    """Serviço responsável por gerar o Token Enriquecido."""

    @staticmethod
    def gerar(
        usuario_id: UUID,
        conta_keycloak: dict,
        perfil: str | None,
        sistema_id: str | None,
    ) -> dict:
        """Gera um Token Enriquecido para um usuário.

        O Token Enriquecido é obtido do cache quando disponível.
        Caso contrário, a projeção do usuário é consultada, um novo
        token é gerado e armazenado em cache.

        O cache é individualizado pela combinação de usuário, perfil e
        sistema.

        Args:
            usuario_id: Identificador único do usuário.
            conta_keycloak: Dados da conta autenticada no Keycloak.
            perfil: Perfil selecionado para composição do token.
            sistema_id: Sistema utilizado para filtrar as permissões,
                quando informado.

        Returns:
            Dados do Token Enriquecido contendo o JWT, a data de
            expiração e as permissões do usuário.
        """
        chave = chaves.token_enriquecido(
            usuario_id=usuario_id,
            perfil=perfil,
            sistema_id=sistema_id,
        )

        resposta = cast(
            dict[str, Any] | None,
            CacheService.obter(chave),
        )

        if resposta is not None:
            logger.info(
                (
                    "Cache hit para o Token Enriquecido do usuário %s "
                    "(perfil=%s, sistema_id=%s)."
                ),
                usuario_id,
                perfil,
                sistema_id,
            )
            return resposta

        logger.info(
            (
                "Cache miss para o Token Enriquecido do usuário %s "
                "(perfil=%s, sistema_id=%s)."
            ),
            usuario_id,
            perfil,
            sistema_id,
        )

        projecao_usuario = TokenEnriquecidoService._obter_projecao_usuario(
            usuario_id=usuario_id,
            sistema_id=sistema_id,
        )

        token, expiracao, permissoes = compor_token_enriquecido(
            conta_keycloak=conta_keycloak,
            projecao_usuario=projecao_usuario,
            perfil=perfil,
        )

        logger.info(
            (
                "Token Enriquecido gerado para o usuário %s "
                "(perfil=%s, sistema_id=%s)."
            ),
            usuario_id,
            perfil,
            sistema_id,
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
            (
                "Token Enriquecido armazenado em cache para o usuário %s "
                "(perfil=%s, sistema_id=%s)."
            ),
            usuario_id,
            perfil,
            sistema_id,
        )

        return resposta

    @staticmethod
    def _obter_projecao_usuario(
        usuario_id: UUID,
        sistema_id: str | None = None,
    ) -> ProjecaoUsuario | None:
        """Obtém a projeção de um usuário.

        A projeção é carregada juntamente com seus perfis e módulos de
        permissão para evitar consultas adicionais durante a geração do
        Token Enriquecido.

        Quando ``sistema_id`` é informado, somente os módulos de permissão
        associados ao sistema são carregados.

        Args:
            usuario_id: Identificador único do usuário.
            sistema_id: Identificador do sistema utilizado para filtrar
                os módulos de permissão.

        Returns:
            Projeção do usuário ou ``None`` caso não exista.
        """
        permissoes_queryset = ModuloPermissaoUsuario.objects.all()

        if sistema_id:
            permissoes_queryset = permissoes_queryset.filter(
                sistema_id=sistema_id,
            )

        return (
            ProjecaoUsuario.objects.prefetch_related(
                "perfis",
                Prefetch(
                    "modulos_permissao",
                    queryset=permissoes_queryset,
                ),
            )
            .filter(usuario_id=usuario_id)
            .first()
        )

    @staticmethod
    def invalidar(usuario_id: UUID) -> None:
        """Invalida todos os Tokens Enriquecidos em cache de um usuário.

        Remove todas as variações de Token Enriquecido associadas ao
        usuário, independentemente do perfil ou sistema utilizado.

        Args:
            usuario_id: Identificador único do usuário.
        """
        CacheService.invalidar_padrao(
            chaves.tokens_enriquecidos_usuario(usuario_id),
        )

        logger.info(
            "Caches do Token Enriquecido invalidados para o usuário %s.",
            usuario_id,
        )

    @staticmethod
    def invalidar_contexto(
        usuario_id: UUID,
        perfil: str | None = None,
        sistema_id: str | None = None,
    ) -> None:
        """Invalida um Token Enriquecido específico em cache.

        Esse método permite invalidar uma única combinação de usuário,
        perfil e sistema. Atualmente, a invalidação principal é realizada
        pelo método ``invalidar``, que remove todos os caches do usuário.

        Args:
            usuario_id: Identificador único do usuário.
            perfil: Identificador do perfil selecionado.
            sistema_id: Identificador do sistema selecionado.
        """
        chave = chaves.token_enriquecido(
            usuario_id=usuario_id,
            perfil=perfil,
            sistema_id=sistema_id,
        )

        CacheService.invalidar(chave)

        logger.info(
            (
                "Cache do Token Enriquecido invalidado para o usuário %s "
                "(perfil=%s, sistema_id=%s)."
            ),
            usuario_id,
            perfil,
            sistema_id,
        )
