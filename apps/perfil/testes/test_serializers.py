"""Testes dos serializers do módulo perfil."""

from uuid import uuid4

from django.test import TestCase

from apps.perfil.api.serializers import ProjecaoUsuarioSerializer
from apps.perfil.models import (
    ModuloPermissaoUsuario,
    PerfilUsuario,
    ProjecaoUsuario,
)


class TestProjecaoUsuarioSerializer(TestCase):
    """Testes do serializer ProjecaoUsuarioSerializer."""

    def setUp(self) -> None:
        """Cria os dados utilizados pelos testes."""
        self.usuario_id = uuid4()

        self.payload = {
            "login": "usuario.teste",
            "rf": "123456",
            "nome": "Usuário Teste",
            "cpf": "12345678900",
            "email": "teste@teste.com",
            "situacao": "ATIVO",
            "dre_codigo": "DRE01",
            "contrato_externo": False,
            "perfis": [
                {
                    "id": uuid4(),
                    "nome": "Administrador",
                    "ativo": True,
                },
                {
                    "id": uuid4(),
                    "nome": "Gestor",
                    "ativo": False,
                },
            ],
            "permissoes": [
                {
                    "sistema_id": 1,
                    "sistema_nome": "CoreSSO",
                    "modulo_id": 3,
                    "modulo_nome": "Usuários",
                    "consultar": True,
                    "inserir": True,
                    "alterar": False,
                    "excluir": False,
                },
                {
                    "sistema_id": 176,
                    "sistema_nome": "Boletim Online",
                    "modulo_id": 1,
                    "modulo_nome": "Boletim Online",
                    "consultar": True,
                    "inserir": True,
                    "alterar": True,
                    "excluir": True,
                },
            ],
        }

    def test_deve_validar_payload_valido(self) -> None:
        """Deve validar um payload válido."""
        serializer = ProjecaoUsuarioSerializer(data=self.payload)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_deve_criar_projecao_usuario(self) -> None:
        """Deve criar uma projeção de usuário."""
        serializer = ProjecaoUsuarioSerializer(data=self.payload)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        usuario = serializer.save(usuario_id=self.usuario_id)

        usuario.refresh_from_db()

        self.assertEqual(ProjecaoUsuario.objects.count(), 1)
        self.assertEqual(usuario.usuario_id, self.usuario_id)
        self.assertEqual(usuario.login, self.payload["login"])
        self.assertEqual(usuario.rf, self.payload["rf"])
        self.assertEqual(usuario.nome, self.payload["nome"])
        self.assertEqual(usuario.cpf, self.payload["cpf"])
        self.assertEqual(usuario.email, self.payload["email"])
        self.assertEqual(usuario.situacao, self.payload["situacao"])
        self.assertEqual(usuario.dre_codigo, self.payload["dre_codigo"])
        self.assertFalse(usuario.contrato_externo)

        self.assertEqual(usuario.perfis.count(), 2)
        self.assertEqual(usuario.modulos_permissao.count(), 2)

    def test_deve_atualizar_projecao_usuario_existente(self) -> None:
        """Deve atualizar uma projeção existente."""
        usuario = ProjecaoUsuario.objects.create(
            usuario_id=self.usuario_id,
            login="login.antigo",
            rf="111111",
            nome="Nome Antigo",
            cpf="11111111111",
            email="antigo@teste.com",
            situacao="INATIVO",
            dre_codigo="DRE00",
            contrato_externo=True,
        )

        PerfilUsuario.objects.create(
            id=uuid4(),
            usuario=usuario,
            nome="Perfil Antigo",
            ativo=True,
        )

        ModuloPermissaoUsuario.objects.create(
            usuario=usuario,
            sistema_id=999,
            sistema_nome="Sistema Antigo",
            modulo_id=1,
            modulo_nome="Módulo Antigo",
        )

        serializer = ProjecaoUsuarioSerializer(data=self.payload)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        usuario = serializer.save(usuario_id=self.usuario_id)

        usuario.refresh_from_db()

        self.assertEqual(ProjecaoUsuario.objects.count(), 1)

        self.assertEqual(usuario.login, self.payload["login"])
        self.assertEqual(usuario.rf, self.payload["rf"])
        self.assertEqual(usuario.nome, self.payload["nome"])
        self.assertEqual(usuario.cpf, self.payload["cpf"])
        self.assertEqual(usuario.email, self.payload["email"])
        self.assertEqual(usuario.situacao, self.payload["situacao"])
        self.assertEqual(usuario.dre_codigo, self.payload["dre_codigo"])
        self.assertFalse(usuario.contrato_externo)

        self.assertEqual(usuario.perfis.count(), 2)
        self.assertEqual(usuario.modulos_permissao.count(), 2)

        self.assertFalse(
            usuario.perfis.filter(nome="Perfil Antigo").exists(),
        )

        self.assertFalse(
            usuario.modulos_permissao.filter(sistema_id=999).exists(),
        )

    def test_deve_substituir_perfis_existentes(self) -> None:
        """Deve substituir os perfis existentes do usuário."""
        usuario = ProjecaoUsuario.objects.create(
            usuario_id=self.usuario_id,
            login="usuario.teste",
            nome="Usuário",
            situacao="ATIVO",
        )

        PerfilUsuario.objects.create(
            id=uuid4(),
            usuario=usuario,
            nome="Perfil Antigo",
            ativo=True,
        )

        serializer = ProjecaoUsuarioSerializer(data=self.payload)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        serializer.save(usuario_id=self.usuario_id)

        usuario.refresh_from_db()

        self.assertEqual(usuario.perfis.count(), 2)

        self.assertFalse(
            usuario.perfis.filter(nome="Perfil Antigo").exists(),
        )

    def test_deve_substituir_permissoes_existentes(self) -> None:
        """Deve substituir as permissões existentes do usuário."""
        usuario = ProjecaoUsuario.objects.create(
            usuario_id=self.usuario_id,
            login="usuario.teste",
            nome="Usuário",
            situacao="ATIVO",
        )

        ModuloPermissaoUsuario.objects.create(
            usuario=usuario,
            sistema_id=999,
            sistema_nome="Sistema Antigo",
            modulo_id=1,
            modulo_nome="Módulo Antigo",
        )

        serializer = ProjecaoUsuarioSerializer(data=self.payload)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        serializer.save(usuario_id=self.usuario_id)

        usuario.refresh_from_db()

        self.assertEqual(usuario.modulos_permissao.count(), 2)

        self.assertFalse(
            usuario.modulos_permissao.filter(sistema_id=999).exists(),
        )
