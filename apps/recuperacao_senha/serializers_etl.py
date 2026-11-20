"""Validação da seção de sistemas de recuperação recebida pelo ETL."""

from typing import Any

from rest_framework import serializers


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
