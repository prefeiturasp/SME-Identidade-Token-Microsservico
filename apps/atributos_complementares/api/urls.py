"""Configuração de rotas da API da aplicação atributos_complementares."""

from django.urls import path

from .views import PushBatchAtributosView

urlpatterns = [
    path(
        "etl/push-batch",
        PushBatchAtributosView.as_view(),
        name="push-batch",
    ),
]
