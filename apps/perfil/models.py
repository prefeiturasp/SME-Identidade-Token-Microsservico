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


class ModuloPermissaoUsuario(models.Model):
    """Registra as permissões CRUD de um usuário por módulo de sistema.

    Modelo fiel à fonte real do CoreSSO (``SYS_GrupoPermissao`` +
    ``SYS_Modulo``): a permissão é concedida por grupo, sistema e
    módulo, com quatro ações independentes — não existe um "código de
    permissão" único no legado, a granularidade real é
    (sistema, módulo, ação). ``sistema_id``/``modulo_id`` usam
    nomenclatura de domínio, não os nomes de coluna de origem
    (``sis_id``/``mod_id``), mesmo padrão de ``dre_codigo`` em
    ``ProjecaoUsuario``. ``modulo_id`` sozinho não é chave natural —
    o mesmo id é reaproveitado em módulos de sistemas diferentes no
    CoreSSO — por isso a unicidade é sempre pelo par
    (sistema_id, modulo_id).
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    usuario = models.ForeignKey(
        ProjecaoUsuario,
        on_delete=models.CASCADE,
        related_name="modulos_permissao",
    )
    sistema_id = models.IntegerField()
    sistema_nome = models.CharField(max_length=255)
    modulo_id = models.IntegerField()
    modulo_nome = models.CharField(max_length=255)
    consultar = models.BooleanField(default=False)
    inserir = models.BooleanField(default=False)
    alterar = models.BooleanField(default=False)
    excluir = models.BooleanField(default=False)

    class Meta:
        """Configurações de metadados do modelo."""

        verbose_name = "Permissão de módulo do usuário"
        verbose_name_plural = "Permissões de módulos do usuário"
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "sistema_id", "modulo_id"],
                name="uniq_modulo_permissao_usuario",
            )
        ]

    def __str__(self) -> str:
        """Retorna sistema e módulo da permissão."""
        return f"{self.sistema_nome} > {self.modulo_nome}"
