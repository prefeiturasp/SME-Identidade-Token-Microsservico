"""Modelos de atributos complementares publicados pelo ETL."""

import uuid

from django.db import models

from apps.perfil.models import ProjecaoUsuario


class AtributoComplementarUsuario(models.Model):
    """Registra os atributos complementares de um usuário.

    Os dados são publicados em lote pelo etl-ms (endpoint
    ``etl/push-batch``) a partir de SE1426, CoreSSO e EOL_DB, e
    identificam o usuário por RF, CPF ou matrícula — o payload de
    origem não carrega o UUID do Keycloak, então o vínculo com
    ``ProjecaoUsuario`` é resolvido de forma oportunista (por RF ou
    CPF) e pode ficar nulo até essa projeção existir.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    usuario = models.ForeignKey(
        ProjecaoUsuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="atributos_complementares",
    )

    rf = models.CharField(max_length=50, db_index=True, null=True, blank=True)
    cpf = models.CharField(max_length=11, db_index=True, null=True, blank=True)
    matricula = models.CharField(
        max_length=50, db_index=True, null=True, blank=True
    )

    nome = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    tipo_usuario = models.CharField(max_length=50, null=True, blank=True)
    cargo = models.CharField(max_length=100, null=True, blank=True)
    funcao = models.CharField(max_length=100, null=True, blank=True)
    unidade = models.CharField(max_length=255, null=True, blank=True)
    unidade_codigo = models.CharField(max_length=50, null=True, blank=True)
    dre = models.CharField(max_length=50, null=True, blank=True)
    ue = models.CharField(max_length=50, null=True, blank=True)
    cod_escola = models.CharField(max_length=20, null=True, blank=True)
    turma = models.CharField(max_length=50, null=True, blank=True)
    tipo_acesso = models.CharField(max_length=50, null=True, blank=True)
    situacao = models.CharField(max_length=20, null=True, blank=True)
    fonte = models.CharField(max_length=50, null=True, blank=True)

    id_execucao = models.UUIDField(null=True, blank=True, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        """Configurações de metadados do modelo."""

        verbose_name = "Atributo complementar de usuário"
        verbose_name_plural = "Atributos complementares de usuários"

    def __str__(self) -> str:
        """Retorna o identificador natural do usuário."""
        return str(self.rf or self.cpf or self.matricula or self.id)


class VinculoAtributoComplementar(models.Model):
    """Um vínculo funcional vigente de um servidor.

    Um servidor pode ter múltiplos vínculos simultâneos e independentes
    (cargo base, cargo sobreposto/comissionado e função/atividade —
    inclusive mais de um cargo base ao mesmo tempo), cada um com seu
    próprio cargo e sua própria unidade/DRE.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    atributo = models.ForeignKey(
        AtributoComplementarUsuario,
        on_delete=models.CASCADE,
        related_name="vinculos",
    )

    tipo_vinculo = models.CharField(max_length=20)
    codigo_vinculo_origem = models.CharField(
        max_length=50,
        help_text="Chave natural do vínculo na origem (SE1426),"
        " usada para upsert idempotente.",
    )

    cargo_codigo = models.CharField(max_length=50, null=True, blank=True)
    cargo_nome = models.CharField(max_length=255, null=True, blank=True)
    unidade_codigo = models.CharField(max_length=50, null=True, blank=True)
    unidade_nome = models.CharField(max_length=255, null=True, blank=True)
    dre_codigo = models.CharField(max_length=50, null=True, blank=True)
    situacao = models.CharField(max_length=50, null=True, blank=True)
    data_inicio = models.CharField(max_length=50, null=True, blank=True)
    vigente = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        """Configurações de metadados do modelo."""

        verbose_name = "Vínculo de atributo complementar"
        verbose_name_plural = "Vínculos de atributos complementares"
        constraints = [
            models.UniqueConstraint(
                fields=["atributo", "tipo_vinculo", "codigo_vinculo_origem"],
                name="vinculo_unico_por_atributo_tipo_origem",
            )
        ]

    def __str__(self) -> str:
        """Retorna o identificador natural do vínculo."""
        return f"{self.tipo_vinculo}:{self.codigo_vinculo_origem}"
