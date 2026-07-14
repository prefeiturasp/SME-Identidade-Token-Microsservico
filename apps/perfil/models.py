"""Modelos relacionados aos usuários, perfis e permissões."""

import uuid

from django.db import models


class ProjecaoUsuario(models.Model):
    """Registra a projeção de um usuário."""

    usuario_id = models.UUIDField(primary_key=True)
    login = models.CharField(max_length=20, unique=True, db_index=True)
    rf = models.CharField(max_length=20, db_index=True, null=True, blank=True)
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=11, db_index=True, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    situacao = models.CharField(max_length=20)
    dre_codigo = models.CharField(max_length=20, null=True, blank=True)
    contrato_externo = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        """Configurações de metadados do modelo."""

        verbose_name = "Projeção de usuário"
        verbose_name_plural = "Projeções de usuários"

    def __str__(self) -> str:
        """Retorna o nome do usuário."""
        return str(self.nome)


class PerfilUsuario(models.Model):
    """Registra os perfis atribuídos a um usuário."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    usuario = models.ForeignKey(
        ProjecaoUsuario,
        on_delete=models.CASCADE,
        related_name="perfis",
    )
    nome = models.CharField(max_length=200)
    ativo = models.BooleanField(default=True)

    class Meta:
        """Configurações de metadados do modelo."""

        verbose_name = "Perfil de usuário"
        verbose_name_plural = "Perfis de usuários"

    def __str__(self) -> str:
        """Retorna o nome do perfil."""
        return str(self.nome)


class PermissaoUsuario(models.Model):
    """Registra as permissões concedidas a um usuário."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    usuario = models.ForeignKey(
        ProjecaoUsuario,
        on_delete=models.CASCADE,
        related_name="permissoes",
    )
    codigo = models.IntegerField()
    descricao = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        """Configurações de metadados do modelo."""

        verbose_name = "Permissão de usuário"
        verbose_name_plural = "Permissões de usuários"

    def __str__(self) -> str:
        """Retorna a descrição da permissão."""
        return str(self.descricao or "")
