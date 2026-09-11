"""Testes da views do módulo perfil."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.perfil.models import (
    ModuloPermissaoUsuario,
    PerfilUsuario,
    ProjecaoUsuario,
)


class TestProjecaoUsuarioView(TestCase):
    """Testes da view ProjecaoUsuarioView."""

    def setUp(self) -> None:
        """Cria os dados utilizados pelos testes."""
        self.client = APIClient()
        self.client.credentials(
            HTTP_X_API_KEY=settings.API_KEY,
        )

        self.usuario_id = uuid4()

        self.url = reverse(
            "projecao-usuario",
            kwargs={
                "usuario_id": self.usuario_id,
            },
        )

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
                    "id": str(uuid4()),
                    "sistema_id": 1,
                    "nome": "Administrador",
                    "ativo": True,
                },
            ],
            "permissoes": [
                {
                    "sistema_id": 1,
                    "sistema_nome": "CoreSSO",
                    "modulo_id": 3,
                    "modulo_nome": "Usuários",
                    "consultar": True,
                    "inserir": False,
                    "alterar": False,
                    "excluir": False,
                },
            ],
        }

    def test_deve_retornar_projecao_usuario(self) -> None:
        """Deve retornar a projeção de um usuário."""
        usuario = ProjecaoUsuario.objects.create(
            usuario_id=self.usuario_id,
            login="usuario.teste",
            rf="123456",
            nome="Usuário Teste",
            cpf="12345678900",
            email="teste@teste.com",
            situacao="ATIVO",
            dre_codigo="DRE01",
            contrato_externo=False,
        )

        PerfilUsuario.objects.create(
            id=uuid4(),
            usuario=usuario,
            sistema_id=1,
            nome="Administrador",
            ativo=True,
        )

        ModuloPermissaoUsuario.objects.create(
            usuario=usuario,
            sistema_id=1,
            sistema_nome="CoreSSO",
            modulo_id=3,
            modulo_nome="Usuários",
            consultar=True,
        )

        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["usuario_id"] == str(self.usuario_id)
        assert response.json()["login"] == usuario.login
        assert response.json()["rf"] == usuario.rf
        assert response.json()["nome"] == usuario.nome
        assert response.json()["cpf"] == usuario.cpf
        assert response.json()["email"] == usuario.email
        assert response.json()["situacao"] == usuario.situacao
        assert response.json()["dre_codigo"] == usuario.dre_codigo
        assert response.json()["contrato_externo"] is False
        assert len(response.json()["perfis"]) == 1
        assert len(response.json()["permissoes"]) == 1
        assert response.json()["perfis"][0]["sistema_id"] == 1

    def test_deve_retornar_400_quando_usuario_nao_existir(
        self,
    ) -> None:
        """Deve retornar 400 quando a projeção não existir."""
        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "detail": "Projeção de usuário não encontrada.",
        }

    def test_deve_sincronizar_projecao_usuario(self) -> None:
        """Deve criar uma nova projeção de usuário."""
        response = self.client.put(
            self.url,
            data=self.payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        usuario = ProjecaoUsuario.objects.get(
            usuario_id=self.usuario_id,
        )

        assert usuario.login == self.payload["login"]
        assert usuario.nome == self.payload["nome"]
        assert usuario.perfis.count() == 1
        assert usuario.modulos_permissao.count() == 1

        perfil = usuario.perfis.first()
        assert perfil is not None
        assert perfil.sistema_id == 1

    def test_deve_atualizar_projecao_usuario(self) -> None:
        """Deve atualizar uma projeção existente."""
        usuario = ProjecaoUsuario.objects.create(
            usuario_id=self.usuario_id,
            login="usuario.teste",
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

        response = self.client.put(
            self.url,
            data=self.payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        usuario.refresh_from_db()

        assert ProjecaoUsuario.objects.count() == 1

        assert usuario.rf == self.payload["rf"]
        assert usuario.nome == self.payload["nome"]
        assert usuario.email == self.payload["email"]
        assert usuario.situacao == self.payload["situacao"]
        assert usuario.dre_codigo == self.payload["dre_codigo"]
        assert usuario.contrato_externo is False

        assert usuario.perfis.count() == 1
        assert usuario.modulos_permissao.count() == 1

        assert not usuario.perfis.filter(
            nome="Perfil Antigo",
        ).exists()

        assert not usuario.modulos_permissao.filter(
            sistema_id=999,
        ).exists()

    def test_deve_retornar_400_quando_payload_for_invalido(
        self,
    ) -> None:
        """Deve retornar erro quando o payload for inválido."""
        payload = self.payload.copy()
        payload.pop("login")

        response = self.client.put(
            self.url,
            data=payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "login" in response.json()

    @patch(
        "apps.perfil.api.serializers.ProjecaoUsuarioSerializer.save",
    )
    def test_deve_retornar_400_quando_ocorrer_erro_na_sincronizacao(
        self,
        mock_save: MagicMock,
    ) -> None:
        """Deve retornar erro quando ocorrer falha na sincronização."""
        mock_save.side_effect = Exception("Erro inesperado")

        response = self.client.put(
            self.url,
            data=self.payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            "detail": ("Ocorreu uma falha ao sincronizar as informações."),
        }

    def test_deve_filtrar_perfis_por_sistema_id(self) -> None:
        """Deve retornar somente perfis associados ao sistema informado."""
        usuario = ProjecaoUsuario.objects.create(
            usuario_id=self.usuario_id,
            login="usuario.teste",
            rf="123456",
            nome="Usuário Teste",
            cpf="12345678900",
            email="teste@teste.com",
            situacao="ATIVO",
            dre_codigo="DRE01",
            contrato_externo=False,
        )

        perfil_sistema_1 = PerfilUsuario.objects.create(
            id=uuid4(),
            usuario=usuario,
            sistema_id=1,
            nome="Administrador",
            ativo=True,
        )

        PerfilUsuario.objects.create(
            id=uuid4(),
            usuario=usuario,
            sistema_id=2,
            nome="Professor",
            ativo=True,
        )

        response = self.client.get(
            self.url,
            {
                "sistema_id": 1,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        corpo = response.json()

        assert len(corpo["perfis"]) == 1

        assert corpo["perfis"][0]["id"] == str(perfil_sistema_1.id)
        assert corpo["perfis"][0]["sistema_id"] == 1
        assert corpo["perfis"][0]["nome"] == "Administrador"

    def test_deve_retornar_400_quando_sistema_id_nao_for_inteiro(
        self,
    ) -> None:
        """Deve retornar 400 quando sistema_id não for inteiro."""
        response = self.client.get(
            self.url,
            {
                "sistema_id": "invalido",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert response.json() == {
            "detail": "O parâmetro sistema_id deve ser número inteiro.",
        }


class TestSistemasUsuarioView(TestCase):
    """Testes da view SistemasUsuarioView."""

    def setUp(self) -> None:
        """Cria os dados utilizados pelos testes."""
        self.client = APIClient()
        self.client.credentials(
            HTTP_X_API_KEY=settings.API_KEY,
        )

        self.usuario_id = uuid4()

        self.url = reverse(
            "sistemas-usuario",
            kwargs={
                "usuario_id": self.usuario_id,
            },
        )

    def test_deve_retornar_sistemas_distintos_do_usuario(self) -> None:
        """Deve retornar os sistemas distintos associados ao usuário."""
        usuario = ProjecaoUsuario.objects.create(
            usuario_id=self.usuario_id,
            login="usuario.teste",
            nome="Usuário Teste",
            situacao="ATIVO",
        )

        ModuloPermissaoUsuario.objects.create(
            usuario=usuario,
            sistema_id=1,
            sistema_nome="CoreSSO",
            modulo_id=3,
            modulo_nome="Usuários",
            consultar=True,
        )

        ModuloPermissaoUsuario.objects.create(
            usuario=usuario,
            sistema_id=1,
            sistema_nome="CoreSSO",
            modulo_id=4,
            modulo_nome="Perfis",
            consultar=True,
        )

        ModuloPermissaoUsuario.objects.create(
            usuario=usuario,
            sistema_id=176,
            sistema_nome="Boletim Online",
            modulo_id=1,
            modulo_nome="Notas",
            consultar=True,
        )

        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK

        corpo = response.json()

        assert corpo["usuario_id"] == str(self.usuario_id)
        assert corpo["sistemas"] == [
            {"sistema_id": 176, "sistema_nome": "Boletim Online"},
            {"sistema_id": 1, "sistema_nome": "CoreSSO"},
        ]

    def test_deve_retornar_lista_vazia_quando_usuario_sem_permissoes(
        self,
    ) -> None:
        """Deve retornar lista vazia quando não houver permissões."""
        ProjecaoUsuario.objects.create(
            usuario_id=self.usuario_id,
            login="usuario.teste",
            nome="Usuário Teste",
            situacao="ATIVO",
        )

        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "usuario_id": str(self.usuario_id),
            "sistemas": [],
        }

    def test_deve_retornar_404_quando_usuario_nao_existir(self) -> None:
        """Deve retornar 404 quando a projeção não existir."""
        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            "detail": "Projeção de usuário não encontrada.",
        }

    def test_deve_exigir_api_key(self) -> None:
        """Deve exigir a API Key para consultar os sistemas."""
        client = APIClient()

        response = client.get(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
