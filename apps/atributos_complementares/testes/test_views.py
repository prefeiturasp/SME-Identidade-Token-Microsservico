"""Testes da views do módulo atributos_complementares."""

from typing import Any
from uuid import uuid4

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.atributos_complementares.models import AtributoComplementarUsuario
from apps.perfil.models import ProjecaoUsuario


class TestPushBatchAtributosView(TestCase):
    """Testes da view PushBatchAtributosView."""

    def setUp(self) -> None:
        """Cria os dados utilizados pelos testes."""
        self.client = APIClient()
        self.client.credentials(
            HTTP_X_API_KEY=settings.API_KEY,
        )

        self.url = reverse("push-batch")

        self.payload: dict[str, Any] = {
            "id_execucao": str(uuid4()),
            "usuarios": [
                {
                    "rf": "1234567",
                    "cpf": "12345678900",
                    "nome": "Usuário Teste",
                    "tipo_usuario": "servidor",
                    "cargo": "Professor",
                    "unidade": "EMEF Teste",
                    "dre": "DRE01",
                    "situacao": "ativo",
                    "fonte": "se1426",
                },
            ],
        }

    def test_deve_criar_atributos_complementares(self) -> None:
        """Deve criar os atributos complementares do lote recebido."""
        response = self.client.post(
            self.url,
            data=self.payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "processados": 1,
            "criados": 1,
            "atualizados": 0,
        }

        atributo = AtributoComplementarUsuario.objects.get(rf="1234567")
        assert atributo.cargo == "Professor"
        assert atributo.unidade == "EMEF Teste"
        assert atributo.dre == "DRE01"

    def test_deve_retornar_401_sem_header_de_autenticacao(self) -> None:
        """Deve rejeitar requisição sem header de API Key."""
        client = APIClient()

        response = client.post(self.url, data=self.payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert AtributoComplementarUsuario.objects.count() == 0

    def test_deve_retornar_401_com_api_key_invalida(self) -> None:
        """Deve rejeitar requisição com API Key incorreta."""
        client = APIClient()
        client.credentials(HTTP_X_API_KEY="chave-invalida")

        response = client.post(self.url, data=self.payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_deve_retornar_400_quando_payload_for_invalido(self) -> None:
        """Deve retornar erro quando nenhum identificador for enviado."""
        payload = {
            "usuarios": [{"nome": "Sem identificador"}],
        }

        response = self.client.post(self.url, data=payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_reenvio_do_mesmo_lote_nao_duplica_registros(self) -> None:
        """Deve atualizar, não duplicar, ao reenviar o mesmo RF."""
        self.client.post(self.url, data=self.payload, format="json")

        usuario_atualizado = dict(self.payload["usuarios"][0])
        usuario_atualizado["cargo"] = "Coordenador"

        payload_atualizado = self.payload.copy()
        payload_atualizado["usuarios"] = [usuario_atualizado]

        response = self.client.post(
            self.url,
            data=payload_atualizado,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "processados": 1,
            "criados": 0,
            "atualizados": 1,
        }

        assert AtributoComplementarUsuario.objects.count() == 1
        atributo = AtributoComplementarUsuario.objects.get(rf="1234567")
        assert atributo.cargo == "Coordenador"

    def test_deve_vincular_projecao_usuario_existente_por_rf(self) -> None:
        """Deve vincular a ProjecaoUsuario existente com o mesmo RF."""
        usuario = ProjecaoUsuario.objects.create(
            usuario_id=uuid4(),
            login="usuario.teste",
            rf="1234567",
            nome="Usuário Teste",
            situacao="ATIVO",
        )

        response = self.client.post(
            self.url,
            data=self.payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        atributo = AtributoComplementarUsuario.objects.get(rf="1234567")
        assert atributo.usuario == usuario

    def test_deve_criar_sem_vinculo_quando_projecao_nao_existir(
        self,
    ) -> None:
        """Deve criar o registro sem vínculo quando não há projeção."""
        response = self.client.post(
            self.url,
            data=self.payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        atributo = AtributoComplementarUsuario.objects.get(rf="1234567")
        assert atributo.usuario is None

    def test_deve_processar_lote_com_multiplos_usuarios(self) -> None:
        """Deve processar corretamente um lote com vários usuários."""
        payload = {
            "id_execucao": str(uuid4()),
            "usuarios": [
                {"rf": "1111111", "nome": "Servidor 1"},
                {"cpf": "22222222222", "nome": "Terceiro 1"},
                {"matricula": "3333333", "nome": "Aluno 1"},
            ],
        }

        response = self.client.post(self.url, data=payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "processados": 3,
            "criados": 3,
            "atualizados": 0,
        }
        assert AtributoComplementarUsuario.objects.count() == 3
