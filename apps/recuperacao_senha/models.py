"""Persistência do fluxo de recuperação compatível com o legado."""

from django.db import models


class SistemaRecuperacaoSenha(models.Model):
    """Configuração do sistema, publicada pelo ETL a partir do legado."""

    codigo_sistema = models.PositiveIntegerField(unique=True)
    nome_sistema = models.CharField(max_length=255)
    pagina_recuperacao_senha = models.URLField(max_length=500)


class RecuperacaoSenha(models.Model):
    """Mantém a solicitação mais recente por contexto e conta."""

    realm = models.CharField(max_length=255)
    usuario_id = models.CharField(max_length=255)
    login = models.CharField(max_length=255)
    token_hash = models.CharField(max_length=64, unique=True, null=True)
    expira_em = models.DateTimeField(null=True)
    operacao_id = models.UUIDField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["realm", "usuario_id"],
                name="recuperacao_identidade_unica",
            ),
        ]


class OperacaoAlteracaoSenha(models.Model):
    """Registra a reserva e o resultado informado pelo Gateway."""

    class Estado(models.TextChoices):
        RESERVADA = "reservada"
        SUCESSO = "sucesso"
        REJEITADA = "rejeitada"
        INCERTA = "incerta"

    id = models.UUIDField(primary_key=True)
    recuperacao = models.ForeignKey(RecuperacaoSenha, on_delete=models.CASCADE)
    token_hash = models.CharField(max_length=64)
    login = models.CharField(max_length=255)
    estado = models.CharField(max_length=20, choices=Estado.choices)
    motivo = models.CharField(max_length=30, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)
