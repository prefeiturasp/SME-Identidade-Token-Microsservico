"""Views da API da aplicação perfil."""

from uuid import UUID

from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.perfil.api.serializers import (
    ProjecaoUsuarioReadSerializer,
    ProjecaoUsuarioSerializer,
)
from apps.perfil.models import ProjecaoUsuario

_TAG = ["Perfil"]


class ProjecaoUsuarioView(APIView):
    """Gerencia a projeção dos usuários."""

    @extend_schema(
        tags=_TAG,
        summary="Consultar projeção de usuário",
        description=(
            "Retorna a projeção de um usuário, "
            "incluindo seus perfis e permissões."
        ),
        responses={
            status.HTTP_200_OK: ProjecaoUsuarioReadSerializer,
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Projeção de usuário não encontrada.",
            ),
        },
    )
    def get(
        self,
        request: Request,
        usuario_id: UUID,
    ) -> Response:
        """Consulta a projeção de um usuário.

        Args:
            request: Requisição HTTP recebida.
            usuario_id: Identificador único do usuário.

        Returns:
            Resposta HTTP contendo a projeção de um usuário.
            Retorna 404 caso a projeção não seja encontrada.
        """
        try:
            usuario = ProjecaoUsuario.objects.prefetch_related(
                "perfis",
                "permissoes",
            ).get(usuario_id=usuario_id)

        except ProjecaoUsuario.DoesNotExist:
            return Response(
                {"detail": "Projeção de usuário não encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProjecaoUsuarioReadSerializer(usuario)

        return Response(serializer.data)

    @extend_schema(
        tags=_TAG,
        summary="Sincronizar projeção de usuário",
        description=(
            "Cria ou atualiza a projeção de autorização utilizada "
            "na geração do token JWT."
        ),
        request=ProjecaoUsuarioSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Projeção sincronizada com sucesso.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Falha ao sincronizar a projeção do usuário.",
            ),
        },
    )
    def put(
        self,
        request: Request,
        usuario_id: UUID,
    ) -> Response:
        """Cria ou atualiza a projeção de um usuário.

        Args:
            request: Requisição HTTP recebida.
            usuario_id: Identificador único do usuário.

        Returns:
            Resposta HTTP indicando o resultado da sincronização.
        """
        serializer = ProjecaoUsuarioSerializer(
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)

        try:
            serializer.save(usuario_id=usuario_id)

        except Exception:
            return Response(
                data={
                    "detail": (
                        "Ocorreu uma falha ao sincronizar as informações."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_200_OK)
