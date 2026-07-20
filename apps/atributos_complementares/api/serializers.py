"""Serializers de entrada do lote de atributos complementares."""

from typing import Any

from rest_framework import serializers


class AtributoComplementarUsuarioEntradaSerializer(serializers.Serializer):
    """Representa os atributos complementares de um usuário do lote."""

    rf = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=50
    )
    cpf = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=11
    )
    matricula = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=50
    )
    nome = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=255
    )
    email = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    tipo_usuario = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=50
    )
    cargo = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=100
    )
    funcao = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=100
    )
    unidade = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=255
    )
    unidade_codigo = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=50
    )
    dre = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=50
    )
    ue = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=50
    )
    cod_escola = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=20
    )
    turma = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=50
    )
    tipo_acesso = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=50
    )
    situacao = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=20
    )
    fonte = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=50
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Exige ao menos um identificador natural do usuário.

        O upsert em ``sincronizar_lote`` depende de RF, CPF ou
        matrícula para localizar o registro existente — sem nenhum
        deles não há como identificar de forma estável a quem os
        atributos pertencem.
        """
        if not (attrs.get("rf") or attrs.get("cpf") or attrs.get("matricula")):
            raise serializers.ValidationError(
                "Ao menos um identificador (rf, cpf ou matricula)"
                " é obrigatório."
            )
        return attrs


class PushBatchSerializer(serializers.Serializer):
    """Representa o lote de atributos complementares enviado pelo ETL."""

    id_execucao = serializers.UUIDField(required=False, allow_null=True)
    usuarios = AtributoComplementarUsuarioEntradaSerializer(many=True)
