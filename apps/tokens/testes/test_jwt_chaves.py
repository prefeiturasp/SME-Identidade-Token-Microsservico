"""Testes dos utilitários de gerenciamento das chaves JWT."""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from apps.tokens.libs.jwt_chaves import (
    _ler_arquivo,
    _obter_configuracao_str,
    listar_chaves_publicas,
    obter_chave_privada,
)


class TestLerArquivo(SimpleTestCase):
    """Testa a leitura de arquivos."""

    @patch("apps.tokens.libs.jwt_chaves.Path.read_text")
    def test_retorna_conteudo_do_arquivo(
        self,
        mock_read_text: MagicMock,
    ) -> None:
        """Testa a leitura do conteúdo de um arquivo."""
        mock_read_text.return_value = "conteudo"

        conteudo = _ler_arquivo("/tmp/chave.pem")

        self.assertEqual(conteudo, "conteudo")
        mock_read_text.assert_called_once_with(
            encoding="utf-8",
        )


@override_settings(
    JWT_ENRIQUECIDO_PRIVATE_KEY_PATH="/tmp/private.pem",
)
class TestObterChavePrivada(SimpleTestCase):
    """Testa a obtenção da chave privada."""

    @patch("apps.tokens.libs.jwt_chaves._ler_arquivo")
    def test_retorna_chave_privada(
        self,
        mock_ler_arquivo: MagicMock,
    ) -> None:
        """Testa a leitura da chave privada configurada."""
        mock_ler_arquivo.return_value = "PRIVATE KEY"

        chave = obter_chave_privada()

        self.assertEqual(
            chave,
            "PRIVATE KEY",
        )

        mock_ler_arquivo.assert_called_once_with(
            "/tmp/private.pem",
        )


@override_settings(
    JWT_ENRIQUECIDO_PUBLIC_KEY_PATH="/tmp/public.pem",
    JWT_ENRIQUECIDO_KID="token-v1",
    JWT_ENRIQUECIDO_ALGORITMO="RS256",
)
class TestListarChavesPublicas(SimpleTestCase):
    """Testa a listagem das chaves públicas."""

    @patch("apps.tokens.libs.jwt_chaves._ler_arquivo")
    def test_retorna_lista_de_chaves_publicas(
        self,
        mock_ler_arquivo: MagicMock,
    ) -> None:
        """Testa a montagem da lista de chaves públicas."""
        mock_ler_arquivo.return_value = "PUBLIC KEY"

        chaves = listar_chaves_publicas()

        self.assertEqual(
            chaves,
            [
                {
                    "kid": "token-v1",
                    "algoritmo": "RS256",
                    "public_key": "PUBLIC KEY",
                }
            ],
        )

        mock_ler_arquivo.assert_called_once_with(
            "/tmp/public.pem",
        )


class TestObterConfiguracaoStr(SimpleTestCase):
    """Testa a validação de configurações obrigatórias."""

    def test_retorna_valor_da_configuracao(
        self,
    ) -> None:
        """Testa o retorno quando a configuração está definida."""
        valor = _obter_configuracao_str(
            "token-v1",
            "JWT_ENRIQUECIDO_KID",
        )

        self.assertEqual(
            valor,
            "token-v1",
        )

    def test_lanca_erro_quando_configuracao_nao_existe(
        self,
    ) -> None:
        """Testa erro quando a configuração não está definida."""
        with self.assertRaisesMessage(
            ValueError,
            ("A configuração JWT_ENRIQUECIDO_KID " "precisa ser definida."),
        ):
            _obter_configuracao_str(
                None,
                "JWT_ENRIQUECIDO_KID",
            )
