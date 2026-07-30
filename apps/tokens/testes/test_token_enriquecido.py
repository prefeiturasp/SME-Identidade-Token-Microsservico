"""Testes da composição do JWT enriquecido."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import TestCase, override_settings

from apps.tokens.token_enriquecido import compor_token_enriquecido

_CONTA_KEYCLOAK = {
    "kc_user_id": "5c29cc47-...",
    "username": "1234567",
    "nome": "FULANO DE TAL",
    "email": "fulano@sme.sp.gov.br",
    "ativo": True,
    "cpf": "12345678900",
    "rf": "1234567",
}


_PRIVATE_KEY = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)


_PRIVATE_KEY_PEM = _PRIVATE_KEY.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)


_PUBLIC_KEY_PEM = _PRIVATE_KEY.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)


def _criar_projecao_usuario() -> MagicMock:
    """Cria uma projeção de usuário simulada para os testes."""
    projecao = MagicMock()

    projecao.rf = "1234567"
    projecao.nome = "FULANO DE TAL"
    projecao.cpf = "12345678900"
    projecao.situacao = "ativo"
    projecao.dre_codigo = "108000"
    projecao.contrato_externo = False

    perfil = MagicMock()
    perfil.id = "b2b2b2b2-..."
    perfil.nome = "professor"
    perfil.ativo = True

    permissao = MagicMock()
    permissao.sistema_id = 1
    permissao.sistema_nome = "CoreSSO"
    permissao.modulo_id = 3
    permissao.modulo_nome = "Usuários"
    permissao.consultar = True
    permissao.inserir = False
    permissao.alterar = False
    permissao.excluir = False

    projecao.perfis.all.return_value = [perfil]
    projecao.modulos_permissao.all.return_value = [permissao]

    return projecao


@override_settings(
    JWT_ENRIQUECIDO_ALGORITMO="RS256",
    JWT_ENRIQUECIDO_KID="token-v1",
    JWT_ENRIQUECIDO_TTL_SEGUNDOS=28800,
)
class TestComporTokenEnriquecido(TestCase):
    """Testa a composição do JWT enriquecido."""

    @patch("apps.tokens.token_enriquecido.obter_chave_privada")
    def test_inclui_claims_do_keycloak_e_do_token_ms(
        self,
        mock_obter_chave_privada: MagicMock,
    ) -> None:
        """Testa a composição do token com dados do Keycloak e projeção."""
        mock_obter_chave_privada.return_value = _PRIVATE_KEY_PEM

        token, _, permissoes = compor_token_enriquecido(
            _CONTA_KEYCLOAK,
            _criar_projecao_usuario(),
            perfil="professor",
        )

        claims = jwt.decode(
            token,
            _PUBLIC_KEY_PEM,
            algorithms=["RS256"],
        )

        self.assertEqual(
            claims["sub"],
            "5c29cc47-...",
        )
        self.assertEqual(
            claims["preferred_username"],
            "1234567",
        )
        self.assertEqual(
            claims["email"],
            "fulano@sme.sp.gov.br",
        )
        self.assertEqual(
            claims["rf"],
            "1234567",
        )
        self.assertEqual(
            claims["dre_codigo"],
            "108000",
        )
        self.assertFalse(
            claims["contrato_externo"],
        )
        self.assertEqual(
            claims["perfis"][0]["nome"],
            "professor",
        )
        self.assertEqual(
            claims["permissoes"][0]["sistema_nome"],
            "CoreSSO",
        )
        self.assertEqual(
            claims["perfilSelecionado"],
            "professor",
        )
        self.assertEqual(
            claims["iss"],
            "sme-token-ms",
        )

        self.assertEqual(
            permissoes,
            claims["permissoes"],
        )

    @patch("apps.tokens.token_enriquecido.obter_chave_privada")
    def test_sem_projecao_token_ms_claims_complementares_ficam_vazias(
        self,
        mock_obter_chave_privada: MagicMock,
    ) -> None:
        """Testa a composição do token sem projeção do usuário."""
        mock_obter_chave_privada.return_value = _PRIVATE_KEY_PEM

        token, _, permissoes = compor_token_enriquecido(
            _CONTA_KEYCLOAK,
            None,
        )

        claims = jwt.decode(
            token,
            _PUBLIC_KEY_PEM,
            algorithms=["RS256"],
        )

        self.assertEqual(
            claims["sub"],
            "5c29cc47-...",
        )
        self.assertEqual(
            claims["rf"],
            "1234567",
        )
        self.assertEqual(
            claims["perfis"],
            [],
        )
        self.assertEqual(
            claims["permissoes"],
            [],
        )
        self.assertEqual(
            permissoes,
            [],
        )
        self.assertNotIn(
            "perfilSelecionado",
            claims,
        )

    @patch("apps.tokens.token_enriquecido.obter_chave_privada")
    def test_sem_perfil_nao_inclui_perfil_selecionado(
        self,
        mock_obter_chave_privada: MagicMock,
    ) -> None:
        """Testa que perfil selecionado não é incluído sem informação."""
        mock_obter_chave_privada.return_value = _PRIVATE_KEY_PEM

        token, _, permissoes = compor_token_enriquecido(
            _CONTA_KEYCLOAK,
            _criar_projecao_usuario(),
        )

        claims = jwt.decode(
            token,
            _PUBLIC_KEY_PEM,
            algorithms=["RS256"],
        )

        self.assertNotIn(
            "perfilSelecionado",
            claims,
        )

        self.assertEqual(
            permissoes,
            claims["permissoes"],
        )

    @override_settings(JWT_ENRIQUECIDO_TTL_SEGUNDOS=60)
    @patch("apps.tokens.token_enriquecido.obter_chave_privada")
    def test_expiracao_reflete_o_ttl_configurado(
        self,
        mock_obter_chave_privada: MagicMock,
    ) -> None:
        """Testa que a expiração respeita o TTL configurado."""
        mock_obter_chave_privada.return_value = _PRIVATE_KEY_PEM

        antes = datetime.now(UTC)

        token, expiracao, permissoes = compor_token_enriquecido(
            _CONTA_KEYCLOAK,
            None,
        )

        claims = jwt.decode(
            token,
            _PUBLIC_KEY_PEM,
            algorithms=["RS256"],
        )

        self.assertEqual(
            claims["exp"] - claims["iat"],
            60,
        )
        self.assertGreaterEqual(
            (expiracao - antes).total_seconds(),
            59,
        )
        self.assertLessEqual(
            (expiracao - antes).total_seconds(),
            61,
        )
        self.assertEqual(
            permissoes,
            [],
        )

    @patch("apps.tokens.token_enriquecido.obter_chave_privada")
    def test_token_nao_decodifica_com_chave_publica_errada(
        self,
        mock_obter_chave_privada: MagicMock,
    ) -> None:
        """Testa que token não valida com chave pública diferente."""
        mock_obter_chave_privada.return_value = _PRIVATE_KEY_PEM

        token, _, _ = compor_token_enriquecido(
            _CONTA_KEYCLOAK,
            None,
        )

        outra_chave = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        outra_publica = outra_chave.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        with self.assertRaises(jwt.InvalidSignatureError):
            jwt.decode(
                token,
                outra_publica,
                algorithms=["RS256"],
            )

    @patch("apps.tokens.token_enriquecido.obter_chave_privada")
    def test_retorna_permissoes_da_projecao(
        self,
        mock_obter_chave_privada: MagicMock,
    ) -> None:
        """Testa que a lista de permissões retornada corresponde às claims."""
        mock_obter_chave_privada.return_value = _PRIVATE_KEY_PEM

        token, _, permissoes = compor_token_enriquecido(
            _CONTA_KEYCLOAK,
            _criar_projecao_usuario(),
        )

        claims = jwt.decode(
            token,
            _PUBLIC_KEY_PEM,
            algorithms=["RS256"],
        )

        self.assertEqual(
            permissoes,
            claims["permissoes"],
        )
        self.assertEqual(
            permissoes[0]["sistema_nome"],
            "CoreSSO",
        )
