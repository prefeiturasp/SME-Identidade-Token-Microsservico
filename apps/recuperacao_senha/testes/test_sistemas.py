"""Carga de sistemas idempotente e validada antes da persistência."""

from typing import Any
from unittest.mock import patch

import pytest
from django.db import DatabaseError
from django.test import override_settings
from drf_spectacular.generators import SchemaGenerator
from rest_framework.test import APIClient

from apps.atributos_complementares.models import AtributoComplementarUsuario
from apps.recuperacao_senha.models import SistemaRecuperacaoSenha

URL = "/identidade-token/api/v1/etl/push-batch"


@pytest.mark.django_db
@override_settings(API_KEY="teste")
def test_carga_idempotente_e_atualizacao() -> None:
    """O código de recuperação identifica o sistema em reenvios do ETL."""
    cliente = APIClient()
    dados: dict[str, Any] = {
        "usuarios": [],
        "sistemas_recuperacao_senha": [
            {
                "codigo_sistema": 1,
                "nome_sistema": "SGP",
                "pagina_recuperacao_senha": "https://sgp.example/redefinir-senha/",
            }
        ],
    }
    assert cliente.post(URL, dados, format="json").status_code == 401
    cliente.credentials(HTTP_X_API_KEY="teste")
    resposta = cliente.post(URL, dados, format="json")
    assert resposta.json()["sistemas_recuperacao_senha"]["criados"] == 1
    assert resposta.json()["processados"] == 0
    resposta = cliente.post(URL, dados, format="json")
    assert resposta.json()["sistemas_recuperacao_senha"]["atualizados"] == 1
    assert SistemaRecuperacaoSenha.objects.count() == 1
    dados["sistemas_recuperacao_senha"][0]["nome_sistema"] = "Novo SGP"
    cliente.post(URL, dados, format="json")
    assert SistemaRecuperacaoSenha.objects.get().nome_sistema == "Novo SGP"


@pytest.mark.django_db
@override_settings(API_KEY="teste")
def test_lote_invalido_nao_grava_parcialmente() -> None:
    """Validação de todo o lote evita salvar apenas parte do cadastro."""
    cliente = APIClient()
    cliente.credentials(HTTP_X_API_KEY="teste")
    dados: dict[str, Any] = {
        "usuarios": [{"rf": "1234567", "nome": "Usuario"}],
        "sistemas_recuperacao_senha": [
            {
                "codigo_sistema": 1,
                "nome_sistema": "SGP",
                "pagina_recuperacao_senha": "https://sgp.example/redefinir-senha/",
            },
            {
                "codigo_sistema": 2,
                "nome_sistema": "Intranet",
                "pagina_recuperacao_senha": "invalido",
            },
        ],
    }
    assert cliente.post(URL, dados, format="json").status_code == 400
    assert not SistemaRecuperacaoSenha.objects.exists()
    assert not AtributoComplementarUsuario.objects.exists()
    dados["sistemas_recuperacao_senha"][1] = dict(
        dados["sistemas_recuperacao_senha"][0]
    )
    assert cliente.post(URL, dados, format="json").status_code == 400
    assert not SistemaRecuperacaoSenha.objects.exists()
    assert not AtributoComplementarUsuario.objects.exists()


@pytest.mark.django_db
@override_settings(API_KEY="teste")
def test_lote_misto_e_omissao_de_sistemas() -> None:
    """Sincroniza ambas as seções e mantém sistemas omitidos ou vazios."""
    cliente = APIClient()
    cliente.credentials(HTTP_X_API_KEY="teste")
    sistema = {
        "codigo_sistema": 1,
        "nome_sistema": "SGP",
        "pagina_recuperacao_senha": "https://sgp.example/redefinir-senha/",
    }
    dados = {
        "usuarios": [{"rf": "1234567"}],
        "sistemas_recuperacao_senha": [sistema],
    }
    resposta = cliente.post(URL, dados, format="json")
    assert resposta.status_code == 200
    assert resposta.json() == {
        "processados": 1,
        "criados": 1,
        "atualizados": 0,
        "sistemas_recuperacao_senha": {
            "processados": 1,
            "criados": 1,
            "atualizados": 0,
        },
    }
    assert AtributoComplementarUsuario.objects.count() == 1
    resposta = cliente.post(URL, {"usuarios": []}, format="json")
    assert resposta.json() == {
        "processados": 0,
        "criados": 0,
        "atualizados": 0,
    }
    resposta = cliente.post(
        URL, {"usuarios": [], "sistemas_recuperacao_senha": []}, format="json"
    )
    assert resposta.json()["sistemas_recuperacao_senha"]["processados"] == 0
    assert SistemaRecuperacaoSenha.objects.count() == 1


@pytest.mark.django_db
@override_settings(API_KEY="teste")
def test_falha_na_carga_de_sistemas_reverte_atributos() -> None:
    """Uma falha na persistência não deixa o lote parcialmente aplicado."""
    cliente = APIClient()
    cliente.credentials(HTTP_X_API_KEY="teste")
    with (
        patch(
            "apps.atributos_complementares.api.views.sincronizar_sistemas",
            side_effect=DatabaseError("falha simulada"),
        ),
        pytest.raises(DatabaseError),
    ):
        cliente.post(
            URL,
            {
                "usuarios": [{"rf": "1234567"}],
                "sistemas_recuperacao_senha": [],
            },
            format="json",
        )
    assert not AtributoComplementarUsuario.objects.exists()


@override_settings(API_KEY="teste")
def test_endpoint_dedicado_nao_e_exposto() -> None:
    """O cadastro de sistemas entra exclusivamente pelo lote do ETL."""
    cliente = APIClient()
    cliente.credentials(HTTP_X_API_KEY="teste")
    removido = "/identidade-token/api/v1/etl/sistemas-recuperacao-senha/"
    assert cliente.post(removido, {}, format="json").status_code == 404
    schema = SchemaGenerator().get_schema(request=None, public=True)
    assert removido not in schema["paths"]
