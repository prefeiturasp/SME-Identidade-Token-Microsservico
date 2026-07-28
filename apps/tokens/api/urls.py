"""Configuração de rotas da API da aplicação tokens."""

from django.urls import path

from apps.tokens.api.views import (
    JWKSView,
    TokenEnriquecidoView,
    ValidarTokenView,
)

urlpatterns = [
    path(
        ".well-known/jwks.json",
        JWKSView.as_view(),
        name="jwks",
    ),
    path(
        "token/enriquecido/<uuid:usuario_id>/",
        TokenEnriquecidoView.as_view(),
        name="token-enriquecido",
    ),
    path(
        "token/validar/",
        ValidarTokenView.as_view(),
        name="token-validar",
    ),
]
