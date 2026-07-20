"""Views da API da aplicação atributos_complementares."""

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

_TAG = ["ETL"]


class PushBatchAtributosView(APIView):
    """Recebe lotes de atributos complementares publicados pelo ETL."""

    @extend_schema(
        tags=_TAG,
        summary="Publicar lote de atributos complementares",
        description=(
            "Cria ou atualiza, em lote, os atributos complementares "
            "(cargo, lotação, DRE/UE, vínculos) de usuários "
            "publicados pelo pipeline do etl-ms."
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
        """Sincroniza o lote de atributos complementares recebido.

        Args:
            request: Requisição HTTP recebida.

        Returns:
            Resposta HTTP com a contagem de registros processados.
        """
        serializer = PushBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resultado = sincronizar_lote(
            serializer.validated_data["usuarios"],
            id_execucao=serializer.validated_data.get("id_execucao"),
        )

        return Response(resultado, status=status.HTTP_200_OK)
