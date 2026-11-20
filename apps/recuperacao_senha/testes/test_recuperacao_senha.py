"""Contrato e controle transacional da recuperação sem provedor externo."""

import re
import uuid
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from datetime import timedelta
from smtplib import SMTPException
from threading import Barrier
from typing import Any, cast
from unittest.mock import patch

import pytest
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.db import close_old_connections, connection
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.recuperacao_senha.dtos import UsuarioIdentidade
from apps.recuperacao_senha.models import (
    OperacaoAlteracaoSenha,
    RecuperacaoSenha,
    SistemaRecuperacaoSenha,
)
from apps.recuperacao_senha.services import recuperacao_senha

BASE = "/identidade-token/api/v1/recuperacao-senha/"
CONTA = UsuarioIdentidade(
    id="conta-1",
    login="1234567",
    nome="Maria",
    email="usuario@example.com",
    ativo=True,
    rf="1234567",
)
CONTEXTO = "identidade-local"


@pytest.fixture(autouse=True)
def configuracao() -> Iterator[None]:
    """Usa apenas banco e caixa de e-mail locais."""
    with override_settings(
        API_KEY="teste",
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="noreply@example.com",
    ):
        yield


@pytest.fixture
def cliente() -> APIClient:
    """Cria o cliente autenticado do Gateway."""
    api = APIClient()
    api.credentials(HTTP_X_API_KEY="teste")
    return api


@pytest.fixture
def sistemas(db: Any) -> None:
    """Mantém dois sistemas para testar substituição entre aplicações."""
    for codigo in (1, 2):
        SistemaRecuperacaoSenha.objects.create(
            codigo_sistema=codigo,
            nome_sistema="SGP",
            pagina_recuperacao_senha="https://sgp.example/redefinir-senha/",
        )


def solicitar(
    cliente: APIClient,
    conta: UsuarioIdentidade | None = CONTA,
    sistema: int = 1,
    contexto: str = CONTEXTO,
) -> Any:
    """Solicita um link a partir dos dados normalizados do Gateway."""
    return cliente.post(
        BASE + "solicitacoes",
        {
            "login": "1234567",
            "sistema": sistema,
            "contexto": contexto,
            "conta": asdict(conta) if conta else None,
        },
        format="json",
    )


def token_email() -> str:
    """Obtém o código somente pela mensagem enviada ao usuário."""
    resultado = re.search(r"[0-9a-f-]{36}", str(mail.outbox[-1].body))
    assert resultado is not None
    return resultado[0]


def validar(
    cliente: APIClient, token: object, contexto: str = CONTEXTO
) -> Any:
    """Consulta a validade sem consumir o código."""
    return cliente.post(
        BASE + "tokens/validar",
        {"token": token, "contexto": contexto},
        format="json",
    )


def reservar(
    cliente: APIClient,
    token: object,
    senha: str = "NovaSenha123",
    conta: UsuarioIdentidade = CONTA,
    operacao: uuid.UUID | str | None = None,
) -> Any:
    """Solicita uma reserva de uso único sem executar alteração remota."""
    return cliente.post(
        BASE + "alteracoes/reservar",
        {
            "token": token,
            "contexto": CONTEXTO,
            "senha": senha,
            "conta": asdict(conta),
            "operacao_id": str(operacao or uuid.uuid4()),
        },
        format="json",
    )


def concluir(
    cliente: APIClient,
    operacao: uuid.UUID | str | None,
    resultado: str = "sucesso",
    motivo: str = "",
) -> Any:
    """Confirma o resultado informado pelo Gateway."""
    return cliente.post(
        BASE + "alteracoes/concluir",
        {
            "contexto": CONTEXTO,
            "operacao_id": str(operacao),
            "resultado": resultado,
            "motivo": motivo,
        },
        format="json",
    )


@pytest.mark.django_db
def test_fluxo_completo_e_confirmacao_idempotente(
    cliente: APIClient, sistemas: None
) -> None:
    """Emite o e-mail, reserva uma vez e confirma sem repetir a operação."""
    assert solicitar(cliente).json() == CONTA.email
    token = token_email()
    registro = RecuperacaoSenha.objects.get()
    assert registro.token_hash == recuperacao_senha.hash_token(token) != token
    assert registro.expira_em is not None
    assert timezone.now() + timedelta(hours=5, minutes=59) < registro.expira_em
    assert registro.expira_em <= timezone.now() + timedelta(hours=6)
    assert "<p>Olá, Maria</p>" in str(
        cast(EmailMultiAlternatives, mail.outbox[-1]).alternatives[0][0]
    )
    assert validar(cliente, token.upper()).json() is True
    assert validar(cliente, token).json() is True
    consulta = cliente.post(
        BASE + "alteracoes/consultar",
        {"contexto": CONTEXTO, "token": token},
        format="json",
    )
    assert consulta.json() == {"usuario_id": CONTA.id, "login": CONTA.login}
    op = uuid.uuid4()
    primeira = reservar(cliente, token, operacao=op)
    assert primeira.status_code == 200
    assert reservar(cliente, token, operacao=op).json() == primeira.json()
    assert OperacaoAlteracaoSenha.objects.count() == 1
    assert validar(cliente, token).json() is False
    assert reservar(cliente, token).status_code == 401
    assert concluir(cliente, op).json() == CONTA.login
    assert concluir(cliente, op).json() == CONTA.login
    assert concluir(cliente, op, "incerta").status_code == 409
    assert reservar(cliente, token, operacao=op).status_code == 409
    registro.refresh_from_db()
    assert registro.token_hash is None and registro.expira_em is None


@pytest.mark.django_db
def test_email_escapa_nome_e_nao_persiste_uuid(
    cliente: APIClient, sistemas: None
) -> None:
    """Preserva o HTML do legado sem injetar marcação do cadastro."""
    solicitar(cliente, replace(CONTA, nome="Maria <Teste> & Silva"))
    html = str(
        cast(EmailMultiAlternatives, mail.outbox[-1]).alternatives[0][0]
    )
    assert "Maria &lt;Teste&gt; &amp; Silva" in html
    assert "<Teste>" not in html
    assert token_email() not in str(RecuperacaoSenha.objects.get().token_hash)


@pytest.mark.django_db
def test_nova_solicitacao_substitui_anterior(
    cliente: APIClient, sistemas: None
) -> None:
    """Uma conta mantém um único link vigente entre sistemas."""
    solicitar(cliente)
    anterior = token_email()
    solicitar(cliente, sistema=2)
    assert validar(cliente, anterior).json() is False
    assert validar(cliente, token_email()).json() is True
    assert RecuperacaoSenha.objects.count() == 1


@pytest.mark.django_db
def test_expiracao_e_isolamento_de_contexto(
    cliente: APIClient, sistemas: None
) -> None:
    """Nenhum contexto consulta tokens de outro nem ultrapassa o prazo."""
    solicitar(cliente)
    token = token_email()
    assert validar(cliente, token, "outro-contexto").json() is False
    RecuperacaoSenha.objects.update(expira_em=timezone.now())
    assert validar(cliente, token).json() is False
    assert reservar(cliente, token).json() == recuperacao_senha.TOKEN_INVALIDO


@pytest.mark.django_db
@pytest.mark.parametrize("token", ["invalido", "", None, {}, []])
def test_token_malformado(cliente: APIClient, token: object) -> None:
    """Valores malformados são rejeitados sem erro interno."""
    assert validar(cliente, token).status_code == 400


@pytest.mark.django_db
def test_uuid_inexistente(cliente: APIClient) -> None:
    """Um UUID desconhecido não permite consulta nem reserva."""
    token = str(uuid.uuid4())
    assert validar(cliente, token).json() is False
    assert reservar(cliente, token).status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize(
    "senha",
    [
        "curta",
        "12345678",
        "abcdefgh",
        "ABCDEFGH",
        "Abcdefgh",
        "Nova Senha1",
        "NovaSenha12345",
        "Sgp@4567",
        "Plateia#4567",
    ],
)
def test_senha_rejeitada_preserva_token(
    cliente: APIClient, sistemas: None, senha: str
) -> None:
    """As regras locais impedem reserva de senha inválida ou padrão."""
    solicitar(cliente)
    token = token_email()
    assert reservar(cliente, token, senha=senha).status_code == 401
    assert validar(cliente, token).json() is True
    assert not OperacaoAlteracaoSenha.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "conta",
    [
        replace(CONTA, id="outra-conta"),
        replace(CONTA, ativo=False),
    ],
)
def test_identidade_da_reserva_nao_pode_ser_trocada(
    cliente: APIClient, sistemas: None, conta: UsuarioIdentidade
) -> None:
    """A reserva permanece vinculada à conta habilitada do link."""
    solicitar(cliente)
    token = token_email()
    assert reservar(cliente, token, conta=conta).status_code == 401
    assert validar(cliente, token).json() is True


@pytest.mark.django_db
@pytest.mark.parametrize("email", ["", None, "invalido", "x@localhost"])
def test_email_invalido(
    cliente: APIClient, sistemas: None, email: str | None
) -> None:
    """Endereços inválidos não produzem solicitação."""
    assert (
        solicitar(cliente, replace(CONTA, email=email)).json()
        == recuperacao_senha.SEM_EMAIL
    )
    assert not RecuperacaoSenha.objects.exists()


@pytest.mark.django_db
def test_conta_ausente_e_sistema_invalido(
    cliente: APIClient, sistemas: None
) -> None:
    """Preserva as mensagens de negócio sem consultar provedor."""
    assert solicitar(cliente, None).json() == "Usuário ou RF não encontrado"
    assert solicitar(cliente, sistema=999).status_code == 400
    assert not RecuperacaoSenha.objects.exists()


@pytest.mark.django_db
def test_falha_de_email_preserva_link_anterior(
    cliente: APIClient, sistemas: None
) -> None:
    """Falha no envio reverte a substituição do código."""
    solicitar(cliente)
    anterior = token_email()
    with patch.object(
        recuperacao_senha, "send_mail", side_effect=SMTPException("falha")
    ):
        assert solicitar(cliente).status_code == 502
    assert validar(cliente, anterior).json() is True


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("motivo", "http", "mensagem"),
    [
        (
            "historico",
            401,
            "A nova senha não pode ser uma das ultimas 5 anteriores",
        ),
        ("padrao", 401, recuperacao_senha.SENHA_INVALIDA),
        (
            "politica",
            502,
            "O histórico de senhas não está configurado no provedor.",
        ),
        (
            "indisponivel",
            502,
            "Não foi possível concluir a recuperação de senha.",
        ),
        ("conta", 401, recuperacao_senha.USUARIO_INVALIDO),
    ],
)
def test_rejeicao_confirmada_libera_nova_tentativa(
    cliente: APIClient,
    sistemas: None,
    motivo: str,
    http: int,
    mensagem: str,
) -> None:
    """Somente confirmação de senha não aplicada restaura o uso do UUID."""
    solicitar(cliente)
    token = token_email()
    op = reservar(cliente, token).json()["operacao_id"]
    resposta = concluir(cliente, op, "rejeitada", motivo)
    assert resposta.status_code == http
    assert resposta.json() == mensagem
    operacao = OperacaoAlteracaoSenha.objects.get(pk=op)
    assert operacao.estado == OperacaoAlteracaoSenha.Estado.REJEITADA
    assert operacao.motivo == motivo
    assert RecuperacaoSenha.objects.get().operacao_id is None
    assert concluir(cliente, op, "rejeitada", motivo).status_code == http
    outro_motivo = "historico" if motivo == "conta" else "conta"
    assert concluir(cliente, op, "rejeitada", outro_motivo).status_code == 409
    assert validar(cliente, token).json() is True
    assert reservar(cliente, token).status_code == 200


@pytest.mark.django_db
def test_resultado_incerto_ou_ausente_nao_libera_uuid(
    cliente: APIClient, sistemas: None
) -> None:
    """Resposta perdida mantém o código reservado, mesmo sem confirmação."""
    solicitar(cliente)
    token = token_email()
    op = reservar(cliente, token).json()["operacao_id"]
    assert validar(cliente, token).json() is False
    assert reservar(cliente, token).status_code == 401
    assert concluir(cliente, op, "incerta").status_code == 502
    assert concluir(cliente, op, "sucesso").status_code == 409
    assert validar(cliente, token).json() is False


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("resultado", "motivo"),
    [
        ("sucesso", ""),
        ("rejeitada", "historico"),
        ("incerta", ""),
    ],
)
def test_conclusao_antiga_nao_afeta_link_substituto(
    cliente: APIClient, sistemas: None, resultado: str, motivo: str
) -> None:
    """Uma operação antiga não invalida nem restaura uma nova solicitação."""
    solicitar(cliente)
    anterior = token_email()
    op = reservar(cliente, anterior).json()["operacao_id"]
    solicitar(cliente, sistema=2)
    novo = token_email()
    concluir(cliente, op, resultado, motivo)
    assert validar(cliente, anterior).json() is False
    assert validar(cliente, novo).json() is True


@pytest.mark.django_db
def test_operacao_de_outro_contexto_nao_pode_ser_confirmada(
    cliente: APIClient, sistemas: None
) -> None:
    """Uma confirmação não pode ultrapassar o contexto autenticado."""
    solicitar(cliente)
    op = reservar(cliente, token_email()).json()["operacao_id"]
    resposta = cliente.post(
        BASE + "alteracoes/concluir",
        {"contexto": "outro", "operacao_id": op, "resultado": "sucesso"},
        format="json",
    )
    assert resposta.status_code == 409
    assert OperacaoAlteracaoSenha.objects.get().estado == "reservada"


@pytest.mark.parametrize(
    "operacao",
    [
        "solicitacoes",
        "tokens/validar",
        "alteracoes/consultar",
        "alteracoes/reservar",
        "alteracoes/concluir",
    ],
)
def test_rotas_internas_exigem_chave(operacao: str) -> None:
    """Somente chamadas autenticadas podem fornecer contas e resultados."""
    assert (
        APIClient().post(BASE + operacao, {}, format="json").status_code == 401
    )


@pytest.mark.django_db(transaction=True)
def test_reservas_concorrentes_tem_um_vencedor(
    cliente: APIClient, sistemas: None
) -> None:
    """Duas chamadas não autorizam a mesma credencial simultaneamente."""
    if not connection.features.has_select_for_update:
        pytest.skip("Exige bloqueio de linha do PostgreSQL")
    solicitar(cliente)
    token = token_email()
    barreira = Barrier(2)

    def executar(_: int) -> str | int:
        close_old_connections()
        try:
            barreira.wait(timeout=10)
            try:
                return recuperacao_senha.reservar_alteracao(
                    token, CONTEXTO, "NovaSenha123", CONTA, uuid.uuid4()
                )["usuario_id"]
            except recuperacao_senha.RecuperacaoSenhaError as erro:
                return erro.status
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert set(executor.map(executar, range(2))) == {CONTA.id, 401}
