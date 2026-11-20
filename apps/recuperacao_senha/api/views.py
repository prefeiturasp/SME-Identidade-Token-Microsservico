"""Operações internas de recuperação orquestradas pelo Gateway."""

from smtplib import SMTPException

from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.recuperacao_senha.api.serializers import (
    ConclusaoSerializer,
    ReservaSerializer,
    SolicitacaoSerializer,
    TokenSerializer,
)
from apps.recuperacao_senha.dtos import UsuarioIdentidade
from apps.recuperacao_senha.services import recuperacao_senha


class RecuperacaoBaseView(APIView):
    """Preserva as mensagens de negócio e oculta falhas de envio."""

    def handle_exception(self, exc: Exception) -> Response:
        """Traduz erros de recuperação sem depender de um provedor."""
        if isinstance(exc, recuperacao_senha.RecuperacaoSenhaError):
            return Response(str(exc), status=exc.status)
        if isinstance(exc, (SMTPException, OSError)):
            return Response(
                "Não foi possível concluir a recuperação de senha.", status=502
            )
        return super().handle_exception(exc)


class SolicitarView(RecuperacaoBaseView):
    """Emite o link usando a conta normalizada pelo Gateway."""

    @extend_schema(
        request=SolicitacaoSerializer,
        responses={200: OpenApiTypes.STR},
        tags=["Recuperação de senha"],
    )
    def post(self, request: Request) -> Response:
        """Valida o sistema, armazena a solicitação e envia o e-mail."""
        entrada = SolicitacaoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        dados = entrada.validated_data
        conta = UsuarioIdentidade(**dados["conta"]) if dados["conta"] else None
        return Response(
            recuperacao_senha.solicitar(
                dados["login"], dados["sistema"], dados["contexto"], conta
            )
        )


class ValidarView(RecuperacaoBaseView):
    """Consulta exclusivamente a validade local do UUID."""

    @extend_schema(
        request=TokenSerializer,
        responses={200: OpenApiTypes.BOOL},
        tags=["Recuperação de senha"],
    )
    def post(self, request: Request) -> Response:
        """Retorna falso para códigos expirados, reservados ou utilizados."""
        entrada = TokenSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        dados = entrada.validated_data
        if not recuperacao_senha.hash_token(dados["token"]):
            return Response("O token informado é inválido", status=400)
        return Response(
            recuperacao_senha.validar(dados["token"], dados["contexto"])
        )


class ConsultarAlteracaoView(RecuperacaoBaseView):
    """Identifica a conta associada ao UUID sem reservar seu uso."""

    @extend_schema(
        request=TokenSerializer,
        responses={200: OpenApiTypes.OBJECT},
        tags=["Recuperação de senha"],
    )
    def post(self, request: Request) -> Response:
        """Retorna a identidade que o Gateway deve consultar."""
        entrada = TokenSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        return Response(
            recuperacao_senha.consultar_alteracao(**entrada.validated_data)
        )


class ReservarAlteracaoView(RecuperacaoBaseView):
    """Autoriza uma única tentativa de alteração de credencial."""

    @extend_schema(
        request=ReservaSerializer,
        responses={200: OpenApiTypes.OBJECT},
        tags=["Recuperação de senha"],
    )
    def post(self, request: Request) -> Response:
        """Valida conta, senha e token antes de reservar a operação."""
        entrada = ReservaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        dados = dict(entrada.validated_data)
        dados["conta"] = UsuarioIdentidade(**dados["conta"])
        return Response(recuperacao_senha.reservar_alteracao(**dados))


class ConcluirAlteracaoView(RecuperacaoBaseView):
    """Registra o resultado sem repetir a alteração no provedor."""

    @extend_schema(
        request=ConclusaoSerializer,
        responses={200: OpenApiTypes.STR},
        tags=["Recuperação de senha"],
    )
    def post(self, request: Request) -> Response:
        """Finaliza a reserva de forma idempotente."""
        entrada = ConclusaoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        return Response(
            recuperacao_senha.concluir_alteracao(**entrada.validated_data)
        )
