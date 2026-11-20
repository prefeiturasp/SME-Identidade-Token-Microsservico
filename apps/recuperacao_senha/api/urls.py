"""Operações internas chamadas pelo Gateway na recuperação de senha."""

from django.urls import path

from apps.recuperacao_senha.api.views import (
    ConcluirAlteracaoView,
    ConsultarAlteracaoView,
    ReservarAlteracaoView,
    SolicitarView,
    ValidarView,
)

app_name = "recuperacao_senha"

urlpatterns = [
    path("solicitacoes", SolicitarView.as_view(), name="solicitar"),
    path("tokens/validar", ValidarView.as_view(), name="validar"),
    path(
        "alteracoes/consultar",
        ConsultarAlteracaoView.as_view(),
        name="consultar-alteracao",
    ),
    path(
        "alteracoes/reservar",
        ReservarAlteracaoView.as_view(),
        name="reservar-alteracao",
    ),
    path(
        "alteracoes/concluir",
        ConcluirAlteracaoView.as_view(),
        name="concluir-alteracao",
    ),
]
