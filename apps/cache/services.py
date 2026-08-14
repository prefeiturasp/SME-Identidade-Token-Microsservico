"""Serviços responsáveis pelas operações de cache."""

import logging
from typing import cast

from django.core.cache import cache

logger = logging.getLogger(__name__)


class CacheService:
    """Serviço responsável pelas operações de cache."""

    @staticmethod
    def obter(chave: str) -> object | None:
        """Obtém um valor armazenado em cache.

        Caso o serviço de cache esteja indisponível, retorna ``None``,
        permitindo que a aplicação continue normalmente.

        Args:
            chave: Chave utilizada para localizar o valor em cache.

        Returns:
            Valor armazenado ou ``None`` caso não exista ou ocorra alguma
            falha durante a consulta.
        """
        try:
            return cast(object | None, cache.get(chave))

        except Exception:
            logger.exception("Falha ao obter valor do cache.")
            return None

    @staticmethod
    def salvar(
        chave: str,
        valor: object,
    ) -> None:
        """Armazena um valor em cache.

        Caso o cache esteja indisponível, registra a ocorrência em log sem
        interromper o fluxo da aplicação.

        Args:
            chave: Chave utilizada para armazenamento.
            valor: Valor que será armazenado.
        Returns:
            None
        """
        try:
            cache.set(
                chave,
                valor,
            )

        except Exception:
            logger.exception("Falha ao salvar valor no cache.")

    @staticmethod
    def invalidar(chave: str) -> None:
        """Remove um valor armazenado em cache.

        Caso o cache esteja indisponível, registra a ocorrência em log sem
        interromper o fluxo da aplicação.

        Args:
            chave: Chave do registro que será removido.
        """
        try:
            cache.delete(chave)

        except Exception:
            logger.exception("Falha ao invalidar valor do cache.")
