"""Testes do models do módulo perfil."""

from uuid import uuid4

from django.test import TestCase

from apps.perfil.models import (
    PerfilUsuario,
    PermissaoUsuario,
    ProjecaoUsuario,
)


class TestProjecaoUsuarioModel(TestCase):
    """Testes do model ProjecaoUsuario."""

    def setUp(self) -> None:
        """Cria uma projeção de usuário."""
        self.usuario = ProjecaoUsuario.objects.create(
            usuario_id=uuid4(),
            login="usuario.teste",
            rf="123456",
            nome="Usuário Teste",
            cpf="12345678900",
            email="teste@teste.com",
            situacao="ATIVO",
            dre_codigo="DRE01",
        )

    def test_deve_criar_projecao_usuario(self) -> None:
        """Deve criar uma projeção de usuário."""
        assert ProjecaoUsuario.objects.count() == 1

        assert self.usuario.login == "usuario.teste"
        assert self.usuario.nome == "Usuário Teste"
        assert self.usuario.contrato_externo is False

    def test_deve_retornar_nome_usuario_no_str(self) -> None:
        """Deve retornar o nome do usuário."""
        assert str(self.usuario) == "Usuário Teste"

    def test_deve_possuir_metadados_corretos(self) -> None:
        """Deve possuir os metadados configurados."""
        meta = ProjecaoUsuario._meta

        assert meta.verbose_name == "Projeção de usuário"
        assert meta.verbose_name_plural == "Projeções de usuários"


class TestPerfilUsuarioModel(TestCase):
    """Testes do model PerfilUsuario."""

    def setUp(self) -> None:
        """Cria um perfil de usuário."""
        usuario = ProjecaoUsuario.objects.create(
            usuario_id=uuid4(),
            login="usuario.teste",
            nome="Usuário Teste",
            situacao="ATIVO",
        )

        self.perfil = PerfilUsuario.objects.create(
            usuario=usuario,
            nome="Administrador",
            ativo=True,
        )

    def test_deve_criar_perfil_usuario(self) -> None:
        """Deve criar um perfil de usuário."""
        assert PerfilUsuario.objects.count() == 1

        assert self.perfil.nome == "Administrador"
        assert self.perfil.ativo is True

    def test_deve_retornar_nome_perfil_no_str(self) -> None:
        """Deve retornar o nome do perfil."""
        assert str(self.perfil) == "Administrador"

    def test_deve_possuir_metadados_corretos(self) -> None:
        """Deve possuir os metadados configurados."""
        meta = PerfilUsuario._meta

        assert meta.verbose_name == "Perfil de usuário"
        assert meta.verbose_name_plural == "Perfis de usuários"

    def test_deve_relacionar_perfil_ao_usuario(self) -> None:
        """Deve relacionar o perfil ao usuário."""
        assert self.perfil.usuario.perfis.count() == 1
        assert self.perfil.usuario.perfis.first() == self.perfil


class TestPermissaoUsuarioModel(TestCase):
    """Testes do model PermissaoUsuario."""

    def setUp(self) -> None:
        """Cria uma permissão de usuário."""
        usuario = ProjecaoUsuario.objects.create(
            usuario_id=uuid4(),
            login="usuario.teste",
            nome="Usuário Teste",
            situacao="ATIVO",
        )

        self.permissao = PermissaoUsuario.objects.create(
            usuario=usuario,
            codigo=100,
            descricao="Consultar usuários",
        )

    def test_deve_criar_permissao_usuario(self) -> None:
        """Deve criar uma permissão de usuário."""
        assert PermissaoUsuario.objects.count() == 1

        assert self.permissao.codigo == 100
        assert self.permissao.descricao == "Consultar usuários"

    def test_deve_retornar_descricao_no_str(self) -> None:
        """Deve retornar a descrição da permissão."""
        assert str(self.permissao) == "Consultar usuários"

    def test_deve_retornar_string_vazia_quando_descricao_for_nula(
        self,
    ) -> None:
        """Deve retornar string vazia quando não houver descrição."""
        usuario = ProjecaoUsuario.objects.create(
            usuario_id=uuid4(),
            login="usuario2",
            nome="Usuário 2",
            situacao="ATIVO",
        )

        permissao = PermissaoUsuario.objects.create(
            usuario=usuario,
            codigo=200,
        )

        assert str(permissao) == ""

    def test_deve_possuir_metadados_corretos(self) -> None:
        """Deve possuir os metadados configurados."""
        meta = PermissaoUsuario._meta

        assert meta.verbose_name == "Permissão de usuário"
        assert meta.verbose_name_plural == "Permissões de usuários"

    def test_deve_relacionar_permissao_ao_usuario(self) -> None:
        """Deve relacionar a permissão ao usuário."""
        assert self.permissao.usuario.permissoes.count() == 1
        assert self.permissao.usuario.permissoes.first() == self.permissao
