"""Regras de recuperação por UUID independentes do provedor de identidade."""

import hashlib
import re
import uuid
from datetime import timedelta
from typing import Any
from uuid import UUID

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from apps.recuperacao_senha.contratos import UsuarioIdentidade
from apps.recuperacao_senha.models import (
    OperacaoAlteracaoSenha,
    RecuperacaoSenha,
    SistemaRecuperacaoSenha,
)

TOKEN_INVALIDO = "Token inválido ou expirado."
SENHA_INVALIDA = (
    "Senha fora do padrão. A senha deve conter entre 8 e 12 "
    "caracteres sem espaços."
)
USUARIO_INVALIDO = "Usuário ou senha incorretos."
SEM_EMAIL = (
    "Você não tem um e-mail cadastrado para recuperar sua senha. "
    "Para restabelecer o seu acesso, procure o Diretor da sua UE ou "
    "Administrador do SGP da sua unidade."
)


class RecuperacaoSenhaError(Exception):
    """Erro de negócio com mensagem e status do contrato legado."""

    def __init__(self, mensagem: str, status: int = 400) -> None:
        super().__init__(mensagem)
        self.status = status


def hash_token(token: object) -> str | None:
    """Normaliza o UUID antes de calcular seu hash, sem armazenar o segredo."""
    try:
        valor = str(uuid.UUID(str(token)))
    except (ValueError, TypeError, AttributeError):
        return None
    return hashlib.sha256(valor.encode()).hexdigest()


def solicitar(
    login: str, sistema: int, contexto: str, conta: UsuarioIdentidade | None
) -> str:
    """Substitui a solicitação anterior e envia um link com validade de 6h."""
    configuracao = SistemaRecuperacaoSenha.objects.filter(
        codigo_sistema=sistema
    ).first()
    if not configuracao:
        raise RecuperacaoSenhaError(
            "O sistema informado não foi identificado na base de "
            "integração do EOL"
        )
    if not conta:
        raise RecuperacaoSenhaError("Usuário ou RF não encontrado")
    if conta.login.casefold() != login.casefold():
        raise RecuperacaoSenhaError(USUARIO_INVALIDO, 401)
    email = conta.email
    if not email or not re.fullmatch(
        r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+"
        r"(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@"
        r"(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+"
        r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?",
        email,
        re.IGNORECASE,
    ):
        raise RecuperacaoSenhaError(SEM_EMAIL)

    token = uuid.uuid4()
    with transaction.atomic():
        registro, _ = RecuperacaoSenha.objects.get_or_create(
            realm=contexto,
            usuario_id=conta.id,
            defaults={"login": login},
        )
        registro = RecuperacaoSenha.objects.select_for_update().get(
            pk=registro.pk
        )
        registro.login = login
        registro.token_hash = hash_token(token)
        registro.expira_em = timezone.now() + timedelta(hours=6)
        registro.operacao_id = None
        registro.save()
        link = configuracao.pagina_recuperacao_senha + str(token)
        nome = conta.nome
        enviados = send_mail(
            f"Recuperação de senha do(a) {configuracao.nome_sistema}",
            f"Olá, {nome}\n\nVocê acionou a opção Esqueci minha senha.\n"
            f"O seu login de acesso continua o mesmo: {login}\n"
            f"O link é válido por apenas 6 horas: {link}",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
            html_message=render_to_string(
                "eol_autenticacao/emails/recuperacao_senha.html",
                {"nome": nome, "login": login, "link": link},
            ),
        )
        if enviados != 1:
            raise RecuperacaoSenhaError(
                "Não foi possível enviar o e-mail de recuperação.", 502
            )
    return email


def validar(token: object, contexto: str) -> bool:
    """Tokens inexistentes, expirados ou consumidos retornam falso."""
    valor = hash_token(token)
    if not valor:
        return False
    return RecuperacaoSenha.objects.filter(
        realm=contexto,
        token_hash=valor,
        expira_em__gt=timezone.now(),
        operacao_id__isnull=True,
    ).exists()


def validar_senha(senha: str, conta: UsuarioIdentidade) -> None:
    """Aplica tamanho, composição e senhas padrão definidos no legado."""
    if (
        not isinstance(senha, str)
        or not 8 <= len(senha) <= 12
        or " " in senha
        or not re.search(r"[A-Z]", senha)
        or not re.search(r"[a-z]", senha)
        or not re.search(r"[0-9!@#$\-%&/\\\[\]|*()_=+]", senha)
    ):
        raise RecuperacaoSenhaError(SENHA_INVALIDA, 401)
    identificador = conta.rf or conta.cpf or conta.login
    sufixo = identificador[-4:]
    padroes = {
        sufixo,
        f"sgp{sufixo}",
        f"sgp@{sufixo}",
        f"sgp#{sufixo}",
        f"plateia@{sufixo}",
        f"plateia#{sufixo}",
    }
    if senha.lower() in padroes:
        raise RecuperacaoSenhaError(
            "A nova senha não pode ser uma senha padrão", 401
        )


def _registro_valido(
    token: str, contexto: str, bloquear: bool = False
) -> RecuperacaoSenha:
    """Localiza uma solicitação disponível, com bloqueio quando solicitado."""
    valor = hash_token(token)
    if not valor:
        raise RecuperacaoSenhaError(TOKEN_INVALIDO, 401)
    registros = RecuperacaoSenha.objects.all()
    if bloquear:
        registros = registros.select_for_update()
    registro = registros.filter(realm=contexto, token_hash=valor).first()
    if registro is None or registro.operacao_id is not None:
        raise RecuperacaoSenhaError(USUARIO_INVALIDO, 401)
    if registro.expira_em is None or registro.expira_em <= timezone.now():
        raise RecuperacaoSenhaError(TOKEN_INVALIDO, 401)
    return registro


def consultar_alteracao(token: str, contexto: str) -> dict[str, str]:
    """Retorna a conta vinculada ao token para consulta pelo Gateway."""
    registro = _registro_valido(token, contexto)
    return {"usuario_id": registro.usuario_id, "login": registro.login}


def _dados_operacao(operacao: OperacaoAlteracaoSenha) -> dict[str, str]:
    """Retorna os dados internos da reserva sem expor o código original."""
    return {
        "operacao_id": str(operacao.id),
        "usuario_id": operacao.recuperacao.usuario_id,
        "login": operacao.login,
    }


@transaction.atomic
def reservar_alteracao(
    token: str,
    contexto: str,
    senha: str,
    conta: UsuarioIdentidade,
    operacao_id: UUID,
) -> dict[str, str]:
    """Valida as regras e reserva o uso único antes da chamada externa.

    Args:
        token: UUID recebido no link de recuperação.
        contexto: Contexto de identidade fornecido pelo Gateway.
        senha: Nova senha, utilizada somente para validação em memória.
        conta: Dados atuais consultados pelo Gateway.
        operacao_id: Identificador idempotente gerado pelo Gateway.

    Returns:
        Identificador da reserva, conta autorizada e login.

    Raises:
        RecuperacaoSenhaError: Se a solicitação ou a senha forem inválidas.
    """
    anterior = OperacaoAlteracaoSenha.objects.filter(pk=operacao_id).first()
    if anterior is not None:
        if (
            anterior.estado == OperacaoAlteracaoSenha.Estado.RESERVADA
            and anterior.token_hash == hash_token(token)
            and anterior.recuperacao.realm == contexto
            and anterior.recuperacao.usuario_id == conta.id
            and anterior.recuperacao.operacao_id == operacao_id
            and anterior.recuperacao.expira_em is not None
            and anterior.recuperacao.expira_em > timezone.now()
        ):
            return _dados_operacao(anterior)
        raise RecuperacaoSenhaError(
            "Operação já utilizada ou substituída.", 409
        )
    registro = _registro_valido(token, contexto, bloquear=True)
    if conta.id != registro.usuario_id or not conta.ativo:
        raise RecuperacaoSenhaError(USUARIO_INVALIDO, 401)
    validar_senha(senha, conta)
    assert registro.token_hash is not None
    operacao = OperacaoAlteracaoSenha.objects.create(
        id=operacao_id,
        recuperacao=registro,
        token_hash=registro.token_hash,
        login=registro.login,
        estado=OperacaoAlteracaoSenha.Estado.RESERVADA,
    )
    registro.operacao_id = operacao_id
    registro.save(update_fields=["operacao_id"])
    return _dados_operacao(operacao)


def concluir_alteracao(
    contexto: str, operacao_id: UUID, resultado: str, motivo: str = ""
) -> str:
    """Confirma o resultado informado pelo Gateway sem afetar novos links.

    Args:
        contexto: Contexto da operação.
        operacao_id: Identificador da reserva autorizada.
        resultado: Sucesso, rejeição confirmada ou resultado incerto.
        motivo: Motivo normalizado de uma rejeição.

    Returns:
        Login associado à operação concluída com sucesso.

    Raises:
        RecuperacaoSenhaError: Se houver rejeição ou confirmação conflitante.
    """
    estados = OperacaoAlteracaoSenha.Estado
    if resultado not in (estados.SUCESSO, estados.REJEITADA, estados.INCERTA):
        raise RecuperacaoSenhaError("Resultado de operação inválido.")
    with transaction.atomic():
        operacao = (
            OperacaoAlteracaoSenha.objects.select_for_update()
            .filter(pk=operacao_id, recuperacao__realm=contexto)
            .first()
        )
        if operacao is None:
            raise RecuperacaoSenhaError("Operação não encontrada.", 409)
        if operacao.estado != estados.RESERVADA:
            if operacao.estado != resultado or operacao.motivo != motivo:
                raise RecuperacaoSenhaError("Operação já finalizada.", 409)
        else:
            operacao.estado = resultado
            operacao.motivo = motivo
            operacao.save(update_fields=["estado", "motivo"])
            campos: dict[str, Any] = {}
            if resultado == estados.SUCESSO:
                campos = {
                    "token_hash": None,
                    "expira_em": None,
                    "operacao_id": None,
                }
            elif resultado == estados.REJEITADA:
                campos = {"operacao_id": None}
            if campos:
                RecuperacaoSenha.objects.filter(
                    pk=operacao.recuperacao_id,
                    token_hash=operacao.token_hash,
                    operacao_id=operacao.id,
                ).update(**campos)
    # O resultado deve ser apresentado depois do commit da transação.
    if operacao.estado == estados.SUCESSO:
        return str(operacao.login)
    if operacao.estado == estados.REJEITADA:
        if operacao.motivo == "conta":
            raise RecuperacaoSenhaError(USUARIO_INVALIDO, 401)
        if operacao.motivo == "historico":
            raise RecuperacaoSenhaError(
                "A nova senha não pode ser uma das ultimas 5 anteriores", 401
            )
        if operacao.motivo == "padrao":
            raise RecuperacaoSenhaError(SENHA_INVALIDA, 401)
        if operacao.motivo == "politica":
            raise RecuperacaoSenhaError(
                "O histórico de senhas não está configurado no provedor.", 502
            )
    raise RecuperacaoSenhaError(
        "Não foi possível concluir a recuperação de senha.", 502
    )
