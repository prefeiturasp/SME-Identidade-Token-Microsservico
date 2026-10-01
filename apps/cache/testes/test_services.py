"""Testes unitários do serviço de cache."""

from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from apps.cache.services import CacheService


class TestCacheService(SimpleTestCase):
    """Testes do serviço responsável pelas operações de cache."""

    @patch("apps.cache.services.cache.get")
    def test_deve_obter_valor_do_cache(
        self,
        mock_get: Mock,
    ) -> None:
        """Deve retornar um valor armazenado em cache.

        Args:
            mock_get: Mock da consulta ao cache.
        """
        mock_get.return_value = "valor"

        resultado = CacheService.obter("chave")

        self.assertEqual(resultado, "valor")

        mock_get.assert_called_once_with("chave")

    @patch("apps.cache.services.logger.exception")
    @patch("apps.cache.services.cache.get")
    def test_deve_retornar_none_quando_ocorrer_erro_ao_obter(
        self,
        mock_get: Mock,
        mock_logger: Mock,
    ) -> None:
        """Deve retornar ``None`` quando ocorrer erro ao consultar o cache."""
        mock_get.side_effect = RuntimeError("Cache indisponível")

        resultado = CacheService.obter("chave")

        self.assertIsNone(resultado)

        mock_get.assert_called_once_with("chave")

        mock_logger.assert_called_once_with(
            "Falha ao obter valor do cache.",
        )

    @patch("apps.cache.services.cache.set")
    def test_deve_salvar_valor_no_cache(
        self,
        mock_set: Mock,
    ) -> None:
        """Deve armazenar um valor em cache.

        Args:
            mock_set: Mock da operação de armazenamento.
        """
        CacheService.salvar(
            chave="chave",
            valor="valor",
        )

        mock_set.assert_called_once_with(
            "chave",
            "valor",
        )

    @patch("apps.cache.services.logger.exception")
    @patch("apps.cache.services.cache.set")
    def test_nao_deve_lancar_excecao_quando_ocorrer_erro_ao_salvar(
        self,
        mock_set: Mock,
        mock_logger: Mock,
    ) -> None:
        """Deve registrar erro quando ocorrer falha ao salvar no cache."""
        mock_set.side_effect = RuntimeError("Cache indisponível")

        CacheService.salvar(
            chave="chave",
            valor="valor",
        )

        mock_set.assert_called_once_with(
            "chave",
            "valor",
        )

        mock_logger.assert_called_once_with(
            "Falha ao salvar valor no cache.",
        )

    @patch("apps.cache.services.cache.delete")
    def test_deve_invalidar_valor_do_cache(
        self,
        mock_delete: Mock,
    ) -> None:
        """Deve remover um valor armazenado em cache.

        Args:
            mock_delete: Mock da operação de remoção.
        """
        CacheService.invalidar("chave")

        mock_delete.assert_called_once_with("chave")

    @patch("apps.cache.services.logger.exception")
    @patch("apps.cache.services.cache.delete")
    def test_nao_deve_lancar_excecao_quando_ocorrer_erro_ao_invalidar(
        self,
        mock_delete: Mock,
        mock_logger: Mock,
    ) -> None:
        """Deve registrar erro quando ocorrer falha ao invalidar o cache."""
        mock_delete.side_effect = RuntimeError("Cache indisponível")

        CacheService.invalidar("chave")

        mock_delete.assert_called_once_with("chave")

        mock_logger.assert_called_once_with(
            "Falha ao invalidar valor do cache.",
        )

    @patch("apps.cache.services.cache.delete_pattern")
    def test_deve_invalidar_valores_do_cache_por_padrao(
        self,
        mock_delete_pattern: Mock,
    ) -> None:
        """Deve remover valores do cache que correspondam ao padrão."""
        padrao = "token-enriquecido:usuario:*"

        CacheService.invalidar_padrao(padrao)

        mock_delete_pattern.assert_called_once_with(
            padrao,
        )

    @patch("apps.cache.services.logger.exception")
    @patch("apps.cache.services.cache.delete_pattern")
    def test_nao_deve_lancar_excecao_quando_ocorrer_erro_ao_invalidar_padrao(
        self,
        mock_delete_pattern: Mock,
        mock_logger: Mock,
    ) -> None:
        """Deve registrar erro quando falhar a invalidação por padrão."""
        mock_delete_pattern.side_effect = RuntimeError("Cache indisponível")

        padrao = "token-enriquecido:usuario:*"

        CacheService.invalidar_padrao(padrao)

        mock_delete_pattern.assert_called_once_with(
            padrao,
        )

        mock_logger.assert_called_once_with(
            "Falha ao invalidar valores do cache pelo padrão."
        )
