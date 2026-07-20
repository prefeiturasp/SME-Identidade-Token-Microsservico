"""Testes do models do módulo perfil."""

from uuid import uuid4

from django.test import TestCase

from apps.perfil.models import (
    ModuloPermissaoUsuario,
    PerfilUsuario,
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


class TestModuloPermissaoUsuarioModel(TestCase):
    """Testes do model ModuloPermissaoUsuario."""

    def setUp(self) -> None:
        """Cria uma permissão de módulo para um usuário."""
        usuario = ProjecaoUsuario.objects.create(
            usuario_id=uuid4(),
            login="usuario.teste",
            nome="Usuário Teste",
            situacao="ATIVO",
        )

        self.permissao = ModuloPermissaoUsuario.objects.create(
            usuario=usuario,
            sistema_id=1,
            sistema_nome="CoreSSO",
            modulo_id=3,
            modulo_nome="Usuários",
            consultar=True,
            inserir=True,
            alterar=False,
            excluir=False,
        )

    def test_deve_criar_permissao_usuario(self) -> None:
        """Deve criar uma permissão de módulo do usuário."""
        assert ModuloPermissaoUsuario.objects.count() == 1

        assert self.permissao.sistema_nome == "CoreSSO"
        assert self.permissao.modulo_nome == "Usuários"
        assert self.permissao.consultar is True
        assert self.permissao.excluir is False

    def test_deve_retornar_sistema_e_modulo_no_str(self) -> None:
        """Deve retornar sistema e módulo formatados na string."""
        assert str(self.permissao) == "CoreSSO > Usuários"

    def test_deve_possuir_metadados_corretos(self) -> None:
        """Deve possuir os metadados configurados."""
        meta = ModuloPermissaoUsuario._meta

        assert meta.verbose_name == "Permissão de módulo do usuário"
        assert meta.verbose_name_plural == "Permissões de módulos do usuário"

    def test_deve_relacionar_permissao_ao_usuario(self) -> None:
        """Deve relacionar a permissão ao usuário."""
        assert self.permissao.usuario.modulos_permissao.count() == 1
        assert (
            self.permissao.usuario.modulos_permissao.first() == self.permissao
        )

    def test_deve_impedir_duplicidade_de_sistema_e_modulo(self) -> None:
        """Deve impedir duas permissões para o mesmo sistema/módulo."""
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            ModuloPermissaoUsuario.objects.create(
                usuario=self.permissao.usuario,
                sistema_id=1,
                sistema_nome="CoreSSO",
                modulo_id=3,
                modulo_nome="Usuários (duplicado)",
            )
