"""Configuração de rotas da API da aplicação perfil."""

from django.urls import path

from .views import ProjecaoUsuarioView

urlpatterns = [
    path(
        "perfis/<uuid:usuario_id>/",
        ProjecaoUsuarioView.as_view(),
        name="projecao-usuario",
    ),
]
