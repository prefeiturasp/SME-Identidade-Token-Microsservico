"""Entrada dos lotes publicados pelo ETL."""

from typing import Any

from django.db import transaction
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.atributos_complementares.api.serializers import (
    PushBatchSerializer,
)
from apps.atributos_complementares.servicos import sincronizar_lote
from apps.recuperacao_senha.services.sistemas import sincronizar_sistemas

_TAG = ["ETL"]


class PushBatchAtributosView(APIView):
    """Recebe os atributos de usuários e as seções opcionais do lote ETL."""

    @extend_schema(
        tags=_TAG,
        summary="Publicar lote do ETL",
        description=(
            "Cria ou atualiza, em lote, os atributos complementares "
            "(cargo, lotação, DRE/UE, vínculos) de usuários e, quando "
            "informados, os sistemas de recuperação de senha. Todas as "
            "seções são validadas antes da gravação."
        ),
        request=PushBatchSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Lote sincronizado com sucesso.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Lote inválido.",
            ),
        },
    )
    def post(self, request: Request) -> Response:
        """Valida e sincroniza as seções do lote na mesma transação.

        Args:
            request: Requisição HTTP recebida.

        Returns:
            Resposta HTTP com a contagem de registros processados.
        """
        serializer = PushBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            resultado: dict[str, Any] = sincronizar_lote(
                serializer.validated_data["usuarios"],
                id_execucao=serializer.validated_data.get("id_execucao"),
            )
            if "sistemas_recuperacao_senha" in serializer.validated_data:
                resultado["sistemas_recuperacao_senha"] = sincronizar_sistemas(
                    serializer.validated_data["sistemas_recuperacao_senha"]
                )

        return Response(resultado, status=status.HTTP_200_OK)
