"""Persistência dos sistemas de recuperação publicados no lote do ETL."""

from typing import Any

from apps.recuperacao_senha.models import SistemaRecuperacaoSenha


def sincronizar_sistemas(sistemas: list[dict[str, Any]]) -> dict[str, int]:
    """Cria ou atualiza os sistemas validados pelo código de recuperação.

    Args:
        sistemas: Cadastros validados pela entrada de lote do ETL.

    Returns:
        Totais de cadastros processados, criados e atualizados.
    """
    criados = 0
    for dados in sistemas:
        _, novo = SistemaRecuperacaoSenha.objects.update_or_create(
            codigo_sistema=dados["codigo_sistema"],
            defaults={
                "nome_sistema": dados["nome_sistema"],
                "pagina_recuperacao_senha": dados["pagina_recuperacao_senha"],
            },
        )
        criados += int(novo)
    return {
        "processados": len(sistemas),
        "criados": criados,
        "atualizados": len(sistemas) - criados,
    }
