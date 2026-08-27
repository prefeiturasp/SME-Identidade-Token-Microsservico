"""Views responsáveis pela publicação do endpoint JWKS."""

import logging
from uuid import UUID

import jwt
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tokens.api.serializers import (
    TokenEnriquecidoRequestSerializer,
    TokenEnriquecidoResponseSerializer,
    ValidarTokenRequestSerializer,
    ValidarTokenResponseSerializer,
)
from apps.tokens.libs.jwks import obter_jwks
from apps.tokens.libs.jwt_validacao import validar_token
from apps.tokens.services import TokenEnriquecidoService

logger = logging.getLogger(__name__)

_TAG = ["Tokens"]


@extend_schema(
    tags=_TAG,
    summary="JWKS",
    description=(
        "Retorna o conjunto de chaves públicas utilizado para validação "
        "dos JWTs."
    ),
    auth=[],
    responses={200: dict},
)
class JWKSView(APIView):
    """Publica o conjunto de chaves públicas no formato JWKS."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """Retorna o conjunto de chaves públicas disponíveis.

        Args:
            request: Requisição HTTP.

        Returns:
            Resposta contendo o documento JWKS.
        """
        logger.info("Consulta ao endpoint JWKS.")

        return Response(obter_jwks())


class TokenEnriquecidoView(APIView):
    """Gera um JWT enriquecido com dados da projeção do usuário."""

    @extend_schema(
        tags=_TAG,
        summary="Gerar token enriquecido",
        description=(
            "Gera um JWT enriquecido utilizando os dados da conta "
            "Keycloak e a projeção de autorização do usuário. "
            "Retorna também as permissões associadas ao usuário."
        ),
        request=TokenEnriquecidoRequestSerializer,
        responses={
            status.HTTP_200_OK: TokenEnriquecidoResponseSerializer,
        },
    )
    def post(
        self,
        request: Request,
        usuario_id: UUID,
    ) -> Response:
        """Gera um JWT enriquecido para o usuário informado.

        O Token-MS busca a projeção de autorização do usuário,
        compõe as claims necessárias e retorna o token JWT assinado
        juntamente com sua data de expiração.

        Args:
            request: Requisição HTTP contendo os dados da conta Keycloak.
            usuario_id: Identificador único do usuário.

        Returns:
            Resposta contendo o token enriquecido gerado, sua data de
            expiração e as permissões associadas ao usuário.
        """
        serializer = TokenEnriquecidoRequestSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        logger.info(
            "Solicitação de geração de Token Enriquecido para o usuário %s.",
            usuario_id,
        )

        resposta = TokenEnriquecidoService.gerar(
            usuario_id=usuario_id,
            conta_keycloak=serializer.validated_data,
            perfil=serializer.validated_data.get("perfil"),
        )

        logger.info(
            "Token Enriquecido gerado para o usuário %s.",
            usuario_id,
        )

        return Response(resposta)


class ValidarTokenView(APIView):
    """Valida um JWT enriquecido."""

    @extend_schema(
        tags=_TAG,
        summary="Validar token enriquecido",
        description=(
            "Valida a assinatura do JWT enriquecido e verifica "
            "se o token não está expirado."
        ),
        request=ValidarTokenRequestSerializer,
        responses={
            status.HTTP_200_OK: ValidarTokenResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Token inválido ou expirado.",
            ),
        },
    )
    def post(
        self,
        request: Request,
    ) -> Response:
        """Valida um JWT enriquecido.

        Args:
            request: Requisição HTTP recebida.

        Returns:
            Resposta contendo o resultado da validação do token.
        """
        serializer = ValidarTokenRequestSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]

        try:
            claims = validar_token(token)

        except jwt.ExpiredSignatureError:
            logger.warning(
                "Falha na validação do Token Enriquecido: token expirado.",
            )

            return Response(
                {
                    "valido": False,
                    "expirado": True,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        except jwt.InvalidTokenError:
            logger.warning(
                "Falha na validação do Token Enriquecido: token inválido.",
            )

            return Response(
                {
                    "valido": False,
                    "expirado": False,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        logger.info(
            "Token Enriquecido validado com sucesso.",
        )

        return Response(
            {
                "valido": True,
                "expirado": False,
                "claims": claims,
            }
        )
