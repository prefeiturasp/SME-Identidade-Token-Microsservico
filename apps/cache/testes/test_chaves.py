"""Testes unitários das funções de geração de chaves de cache."""

from uuid import UUID

from django.test import SimpleTestCase

from apps.cache import chaves


class TestChavesCache(SimpleTestCase):
    """Testes das funções responsáveis pela geração das chaves de cache."""

    def test_deve_gerar_chave_token_enriquecido_sem_perfil_e_sistema(
        self,
    ) -> None:
        """Deve utilizar ``none`` se perfil ou sistema não forem informados."""
        usuario_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        resultado = chaves.token_enriquecido(
            usuario_id=usuario_id,
            perfil=None,
            sistema_id=None,
        )

        self.assertEqual(
            resultado,
            (
                "token-enriquecido:"
                "550e8400-e29b-41d4-a716-446655440000:"
                "none:none"
            ),
        )

    def test_deve_gerar_chave_token_enriquecido_com_perfil_e_sistema(
        self,
    ) -> None:
        """Deve utilizar perfil e sistema na composição da chave."""
        usuario_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        resultado = chaves.token_enriquecido(
            usuario_id=usuario_id,
            perfil="000ea900-821a-402b-9da0-315596a466ee",
            sistema_id="102",
        )

        self.assertEqual(
            resultado,
            (
                "token-enriquecido:"
                "550e8400-e29b-41d4-a716-446655440000:"
                "000ea900-821a-402b-9da0-315596a466ee:"
                "102"
            ),
        )

    def test_deve_gerar_chave_token_enriquecido_sem_perfil_com_sistema(
        self,
    ) -> None:
        """Deve permitir sistema informado sem perfil."""
        usuario_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        resultado = chaves.token_enriquecido(
            usuario_id=usuario_id,
            perfil=None,
            sistema_id="102",
        )

        self.assertEqual(
            resultado,
            (
                "token-enriquecido:"
                "550e8400-e29b-41d4-a716-446655440000:"
                "none:102"
            ),
        )

    def test_deve_gerar_padrao_dos_tokens_enriquecidos_do_usuario(
        self,
    ) -> None:
        """Deve gerar o padrão para todas as chaves de um usuário."""
        usuario_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        resultado = chaves.tokens_enriquecidos_usuario(
            usuario_id,
        )

        self.assertEqual(
            resultado,
            ("token-enriquecido:" "550e8400-e29b-41d4-a716-446655440000:*"),
        )
