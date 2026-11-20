"""Validação das operações de recuperação e da carga de sistemas."""

from typing import Any

from rest_framework import serializers


class ContextoSerializer(serializers.Serializer):
    """Contexto de identidade informado pelo Gateway autenticado."""

    contexto = serializers.CharField(max_length=255, trim_whitespace=False)


class ContaSerializer(serializers.Serializer):
    """Dados normalizados consultados pelo Gateway."""

    id = serializers.CharField(max_length=255)
    login = serializers.CharField(max_length=255, trim_whitespace=False)
    nome = serializers.CharField(allow_blank=True)
    email = serializers.CharField(allow_null=True, allow_blank=True)
    ativo = serializers.BooleanField()
    rf = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    cpf = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )


class SolicitacaoSerializer(ContextoSerializer):
    """Solicitação com a conta obtida pelo Gateway."""

    login = serializers.CharField(trim_whitespace=False)
    sistema = serializers.IntegerField()
    conta = ContaSerializer(allow_null=True)


class TokenSerializer(ContextoSerializer):
    """Token e contexto consultados sem comunicação com o provedor."""

    token = serializers.CharField(trim_whitespace=False)


class ReservaSerializer(TokenSerializer):
    """Dados da reserva e conta atual vinculada ao token."""

    senha = serializers.CharField(trim_whitespace=False, write_only=True)
    conta = ContaSerializer()
    operacao_id = serializers.UUIDField()


class ConclusaoSerializer(ContextoSerializer):
    """Resultado normalizado informado pelo Gateway."""

    operacao_id = serializers.UUIDField()
    resultado = serializers.ChoiceField(
        choices=["sucesso", "rejeitada", "incerta"]
    )
    motivo = serializers.ChoiceField(
        choices=[
            "",
            "historico",
            "padrao",
            "politica",
            "indisponivel",
            "conta",
        ],
        default="",
        required=False,
    )


class ListaSistemasRecuperacaoSerializer(serializers.ListSerializer):
    """Valida a unicidade dos códigos na seção do lote."""

    def validate(self, sistemas: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Recusa códigos duplicados antes de persistir o lote.

        Args:
            sistemas: Cadastros cujos campos já foram validados.

        Returns:
            Cadastros sem códigos duplicados.

        Raises:
            serializers.ValidationError: Se o mesmo código aparecer novamente.
        """
        codigos = [item["codigo_sistema"] for item in sistemas]
        if len(codigos) != len(set(codigos)):
            raise serializers.ValidationError(
                "Código de sistema duplicado no lote."
            )
        return sistemas


class SistemaRecuperacaoSerializer(serializers.Serializer):
    """Cadastro independente dos identificadores de sistema do CoreSSO."""

    codigo_sistema = serializers.IntegerField(min_value=1)
    nome_sistema = serializers.CharField(max_length=255)
    pagina_recuperacao_senha = serializers.URLField(max_length=500)

    class Meta:
        list_serializer_class = ListaSistemasRecuperacaoSerializer
