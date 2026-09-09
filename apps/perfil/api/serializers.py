"""Serializers do domínio de autorização."""

from typing import Any

from django.db import transaction
from rest_framework import serializers

from apps.perfil.models import (
    ModuloPermissaoUsuario,
    PerfilUsuario,
    ProjecaoUsuario,
)


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    """Representa os perfis associados a um usuário."""

    id = serializers.UUIDField()

    class Meta:
        model = PerfilUsuario
        fields = (
            "id",
            "sistema_id",
            "nome",
            "ativo",
        )


class ModuloPermissaoUsuarioSerializer(serializers.ModelSerializer):
    """Representa as permissões de um módulo concedidas a um usuário."""

    class Meta:
        model = ModuloPermissaoUsuario
        fields = (
            "sistema_id",
            "sistema_nome",
            "modulo_id",
            "modulo_nome",
            "consultar",
            "inserir",
            "alterar",
            "excluir",
        )


class ProjecaoUsuarioSerializer(serializers.ModelSerializer):
    """Representa a projeção de um usuário."""

    login = serializers.CharField(
        validators=[],
    )

    perfis = PerfilUsuarioSerializer(many=True)
    permissoes = ModuloPermissaoUsuarioSerializer(many=True)

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
                    sistema_id=perfil.get("sistema_id"),
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
        usuario.modulos_permissao.all().delete()

        ModuloPermissaoUsuario.objects.bulk_create(
            [
                ModuloPermissaoUsuario(
                    usuario=usuario,
                    sistema_id=permissao["sistema_id"],
                    sistema_nome=permissao["sistema_nome"],
                    modulo_id=permissao["modulo_id"],
                    modulo_nome=permissao["modulo_nome"],
                    consultar=permissao["consultar"],
                    inserir=permissao["inserir"],
                    alterar=permissao["alterar"],
                    excluir=permissao["excluir"],
                )
                for permissao in permissoes
            ]
        )


class SistemaUsuarioSerializer(serializers.Serializer):
    """Representa um sistema distinto associado a um usuário."""

    sistema_id = serializers.IntegerField()
    sistema_nome = serializers.CharField()


class SistemasUsuarioResponseSerializer(serializers.Serializer):
    """Representa a lista de sistemas distintos de um usuário."""

    usuario_id = serializers.UUIDField()
    sistemas = SistemaUsuarioSerializer(many=True)


class ProjecaoUsuarioReadSerializer(serializers.ModelSerializer):
    """Representa a projeção de usuário para consulta."""

    perfis = PerfilUsuarioSerializer(many=True, read_only=True)
    permissoes = ModuloPermissaoUsuarioSerializer(
        many=True, read_only=True, source="modulos_permissao"
    )

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
