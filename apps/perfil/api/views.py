"""Views da API da aplicação perfil."""

import logging
from uuid import UUID

from django.db.models import Prefetch
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
)
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.perfil.api.serializers import (
    ProjecaoUsuarioReadSerializer,
    ProjecaoUsuarioSerializer,
    SistemasUsuarioResponseSerializer,
)
from apps.perfil.models import (
    ModuloPermissaoUsuario,
    PerfilUsuario,
    ProjecaoUsuario,
)
from apps.tokens.services import TokenEnriquecidoService

logger = logging.getLogger(__name__)

_TAG = ["Perfil"]


class ProjecaoUsuarioView(APIView):
    """Gerencia a projeção dos usuários."""

    @extend_schema(
        tags=_TAG,
        summary="Consultar projeção de usuário",
        description=(
            "Retorna a projeção de um usuário, "
            "incluindo seus perfis e permissões. "
            "Quando sistema_id é informado, os perfis são filtrados "
            "pelo sistema."
        ),
        parameters=[
            OpenApiParameter(
                name="sistema_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Identificador do sistema.",
            ),
        ],
        responses={
            status.HTTP_200_OK: ProjecaoUsuarioReadSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
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

        Quando ``sistema_id`` é informado via query string, somente
        os perfis associados ao sistema são retornados.

        Args:
            request: Requisição HTTP recebida.
            usuario_id: Identificador único do usuário.

        Returns:
            Resposta HTTP contendo a projeção de um usuário.
            Retorna 400 caso a projeção não seja encontrada.
        """
        sistema_id_param = request.query_params.get("sistema_id")

        perfis_queryset = PerfilUsuario.objects.all()

        if sistema_id_param is not None:
            try:
                sistema_id = int(sistema_id_param)
            except ValueError:
                return Response(
                    {
                        "detail": (
                            "O parâmetro sistema_id deve ser número inteiro."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            perfis_queryset = perfis_queryset.filter(
                sistema_id=sistema_id,
            )

        try:
            usuario = ProjecaoUsuario.objects.prefetch_related(
                Prefetch(
                    "perfis",
                    queryset=perfis_queryset,
                ),
                "modulos_permissao",
            ).get(usuario_id=usuario_id)

        except ProjecaoUsuario.DoesNotExist:
            logger.warning(
                "Projeção do usuário %s não encontrada.",
                usuario_id,
            )

            return Response(
                {"detail": "Projeção de usuário não encontrada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(
            "Projeção do usuário %s consultada com sucesso.",
            usuario_id,
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

        logger.info(
            "Iniciando sincronização da projeção do usuário %s.",
            usuario_id,
        )

        try:
            serializer.save(usuario_id=usuario_id)

        except Exception:
            logger.exception(
                "Falha ao sincronizar a projeção do usuário %s.",
                usuario_id,
            )

            return Response(
                data={
                    "detail": (
                        "Ocorreu uma falha ao sincronizar as informações."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        TokenEnriquecidoService.invalidar(usuario_id)

        logger.info(
            "Projeção do usuário %s sincronizada com sucesso.",
            usuario_id,
        )

        return Response(status=status.HTTP_200_OK)


class SistemasUsuarioView(APIView):
    """Consulta os sistemas distintos associados a um usuário."""

    @extend_schema(
        tags=_TAG,
        summary="Consultar sistemas do usuário",
        description=(
            "Retorna a lista de sistemas distintos aos quais o "
            "usuário tem acesso, derivada de suas permissões de "
            "módulo."
        ),
        responses={
            status.HTTP_200_OK: SistemasUsuarioResponseSerializer,
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
        """Consulta os sistemas distintos de um usuário.

        Args:
            request: Requisição HTTP recebida.
            usuario_id: Identificador único do usuário.

        Returns:
            Resposta HTTP contendo os sistemas do usuário. Retorna
            404 caso a projeção não exista para o usuário informado.
        """
        if not ProjecaoUsuario.objects.filter(
            usuario_id=usuario_id,
        ).exists():
            logger.warning(
                "Projeção do usuário %s não encontrada.",
                usuario_id,
            )

            return Response(
                {"detail": "Projeção de usuário não encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        sistemas = (
            ModuloPermissaoUsuario.objects.filter(
                usuario_id=usuario_id,
            )
            .values("sistema_id", "sistema_nome")
            .distinct()
            .order_by("sistema_nome")
        )

        logger.info(
            "Sistemas do usuário %s consultados com sucesso.",
            usuario_id,
        )

        serializer = SistemasUsuarioResponseSerializer(
            {"usuario_id": usuario_id, "sistemas": sistemas},
        )

        return Response(serializer.data)
