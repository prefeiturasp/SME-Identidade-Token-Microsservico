"""Testes unitários do serviço de geração do Token Enriquecido."""

from datetime import UTC, datetime
from unittest.mock import Mock, patch
from uuid import uuid4

from django.db.models import Prefetch
from django.test import SimpleTestCase

from apps.tokens.services import TokenEnriquecidoService


class TokenEnriquecidoServiceTest(SimpleTestCase):
    """Testes do serviço responsável pela geração do Token Enriquecido."""

    @patch("apps.tokens.services.CacheService.obter")
    def test_deve_retornar_token_do_cache(
        self,
        mock_obter: Mock,
    ) -> None:
        """Deve retornar o Token Enriquecido quando existir em cache."""
        usuario_id = uuid4()

        resposta = {
            "token": "jwt",
            "data_expiracao": datetime.now(UTC),
            "permissoes": ["ADMIN"],
        }

        mock_obter.return_value = resposta

        resultado = TokenEnriquecidoService.gerar(
            usuario_id=usuario_id,
            conta_keycloak={},
            perfil=None,
            sistema_id=None,
        )

        self.assertEqual(resultado, resposta)

        mock_obter.assert_called_once()

    @patch("apps.tokens.services.CacheService.salvar")
    @patch("apps.tokens.services.compor_token_enriquecido")
    @patch(
        "apps.tokens.services.TokenEnriquecidoService._obter_projecao_usuario"
    )
    @patch("apps.tokens.services.CacheService.obter")
    def test_deve_gerar_token_quando_cache_nao_existir(
        self,
        mock_obter: Mock,
        mock_obter_projecao: Mock,
        mock_compor: Mock,
        mock_salvar: Mock,
    ) -> None:
        """Deve gerar e armazenar Token Enriquecido quando não houver cache."""
        usuario_id = uuid4()
        expiracao = datetime.now(UTC)

        mock_obter.return_value = None

        projecao = Mock()
        mock_obter_projecao.return_value = projecao

        mock_compor.return_value = (
            "jwt",
            expiracao,
            ["ADMIN"],
        )

        resultado = TokenEnriquecidoService.gerar(
            usuario_id=usuario_id,
            conta_keycloak={},
            perfil="ADMIN",
            sistema_id="102",
        )

        self.assertEqual(
            resultado,
            {
                "token": "jwt",
                "data_expiracao": expiracao,
                "permissoes": ["ADMIN"],
            },
        )

        mock_obter_projecao.assert_called_once_with(
            usuario_id,
            sistema_id="102",
        )

        mock_compor.assert_called_once_with(
            conta_keycloak={},
            projecao_usuario=projecao,
            perfil="ADMIN",
        )

        mock_salvar.assert_called_once()

    @patch("apps.tokens.services.ProjecaoUsuario.objects")
    def test_deve_obter_projecao_usuario(
        self,
        mock_objects: Mock,
    ) -> None:
        """Deve retornar a projeção do usuário."""
        usuario_id = uuid4()
        projecao = Mock()

        (
            mock_objects.prefetch_related.return_value.filter.return_value.first.return_value
        ) = projecao

        resultado = TokenEnriquecidoService._obter_projecao_usuario(
            usuario_id,
            sistema_id=None,
        )

        self.assertEqual(resultado, projecao)

        mock_objects.prefetch_related.assert_called_once()

        args = mock_objects.prefetch_related.call_args.args

        self.assertEqual(args[0], "perfis")
        self.assertIsInstance(args[1], Prefetch)
        self.assertEqual(
            args[1].prefetch_through,
            "modulos_permissao",
        )

        mock_objects.prefetch_related.return_value.filter.assert_called_once_with(
            usuario_id=usuario_id,
        )

        (
            mock_objects.prefetch_related.return_value.filter.return_value.first
        ).assert_called_once_with()

    @patch("apps.tokens.services.CacheService.invalidar")
    @patch("apps.tokens.services.chaves.token_enriquecido")
    def test_deve_invalidar_cache(
        self,
        mock_chave: Mock,
        mock_invalidar: Mock,
    ) -> None:
        """Deve invalidar o Token Enriquecido armazenado em cache."""
        usuario_id = uuid4()

        mock_chave.return_value = "token:1"

        TokenEnriquecidoService.invalidar(usuario_id)

        mock_chave.assert_called_once_with(usuario_id)

        mock_invalidar.assert_called_once_with("token:1")

    @patch("apps.tokens.services.ProjecaoUsuario.objects")
    @patch("apps.tokens.services.ModuloPermissaoUsuario.objects")
    @patch("apps.tokens.services.Prefetch")
    def test_deve_filtrar_permissoes_por_sistema(
        self,
        mock_prefetch: Mock,
        mock_permissoes_objects: Mock,
        mock_projecao_objects: Mock,
    ) -> None:
        """Deve filtrar as permissões quando sistema_id for informado."""
        usuario_id = uuid4()
        projecao = Mock()

        permissoes_queryset = Mock()
        permissoes_filtradas = Mock()
        prefetch = Mock()

        mock_permissoes_objects.all.return_value = permissoes_queryset
        permissoes_queryset.filter.return_value = permissoes_filtradas
        mock_prefetch.return_value = prefetch

        (
            mock_projecao_objects.prefetch_related.return_value.filter.return_value.first.return_value
        ) = projecao

        resultado = TokenEnriquecidoService._obter_projecao_usuario(
            usuario_id,
            sistema_id="102",
        )

        self.assertEqual(resultado, projecao)

        mock_permissoes_objects.all.assert_called_once_with()

        permissoes_queryset.filter.assert_called_once_with(
            sistema_id="102",
        )

        mock_prefetch.assert_called_once_with(
            "modulos_permissao",
            queryset=permissoes_filtradas,
        )

        mock_projecao_objects.prefetch_related.assert_called_once_with(
            "perfis",
            prefetch,
        )

        mock_projecao_objects.prefetch_related.return_value.filter.assert_called_once_with(
            usuario_id=usuario_id,
        )

        (
            mock_projecao_objects.prefetch_related.return_value.filter.return_value.first
        ).assert_called_once_with()
