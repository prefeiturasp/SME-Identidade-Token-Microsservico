"""Serializers do domínio de autorização."""

from typing import Any

from django.db import transaction
from rest_framework import serializers

from apps.perfil.models import (
    PerfilUsuario,
    PermissaoUsuario,
    ProjecaoUsuario,
)


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    """Representa os perfis associados a um usuário."""

    id = serializers.UUIDField()

    class Meta:
        model = PerfilUsuario
        fields = (
            "id",
            "nome",
            "ativo",
        )


class PermissaoUsuarioSerializer(serializers.ModelSerializer):
    """Representa as permissões concedidas a um usuário."""

    class Meta:
        model = PermissaoUsuario
        fields = (
            "codigo",
            "descricao",
        )


class ProjecaoUsuarioSerializer(serializers.ModelSerializer):
    """Representa a projeção de um usuário."""

    login = serializers.CharField(
        validators=[],
    )

    perfis = PerfilUsuarioSerializer(many=True)
    permissoes = PermissaoUsuarioSerializer(many=True)

    class Meta:
        model = ProjecaoUsuario
        fields = (
            "login",
            "rf",
            "nome",
            "cpf",
            "email",
            "situacao",
            "dre_codigo",
            "contrato_externo",
            "perfis",
            "permissoes",
        )

    @transaction.atomic
    def save(self, **kwargs: Any) -> ProjecaoUsuario:
        """Cria ou atualiza a projeção do usuário."""
        usuario_id = kwargs["usuario_id"]
        dados = self.validated_data

        perfis = dados.pop("perfis")
        permissoes = dados.pop("permissoes")

        usuario: ProjecaoUsuario

        usuario, _ = ProjecaoUsuario.objects.update_or_create(
            usuario_id=usuario_id,
            defaults=dados,
        )

        self._sincronizar_perfis(usuario, perfis)
        self._sincronizar_permissoes(usuario, permissoes)

        return usuario

    @staticmethod
    def _sincronizar_perfis(
        usuario: ProjecaoUsuario,
        perfis: list[dict],
    ) -> None:
        """Substitui os perfis associados ao usuário."""
        usuario.perfis.all().delete()

        PerfilUsuario.objects.bulk_create(
            [
                PerfilUsuario(
                    id=perfil["id"],
                    usuario=usuario,
                    nome=perfil["nome"],
                    ativo=perfil["ativo"],
                )
                for perfil in perfis
            ]
        )

    @staticmethod
    def _sincronizar_permissoes(
        usuario: ProjecaoUsuario,
        permissoes: list[dict],
    ) -> None:
        """Substitui as permissões associadas ao usuário."""
        usuario.permissoes.all().delete()

        PermissaoUsuario.objects.bulk_create(
            [
                PermissaoUsuario(
                    usuario=usuario,
                    codigo=permissao["codigo"],
                    descricao=permissao["descricao"],
                )
                for permissao in permissoes
            ]
        )


class ProjecaoUsuarioReadSerializer(serializers.ModelSerializer):
    """Representa a projeção de usuário para consulta."""

    perfis = PerfilUsuarioSerializer(many=True, read_only=True)
    permissoes = PermissaoUsuarioSerializer(many=True, read_only=True)

    class Meta:
        model = ProjecaoUsuario
        fields = (
            "usuario_id",
            "login",
            "rf",
            "nome",
            "cpf",
            "email",
            "situacao",
            "dre_codigo",
            "contrato_externo",
            "perfis",
            "permissoes",
        )
