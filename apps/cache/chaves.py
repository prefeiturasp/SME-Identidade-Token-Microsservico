"""Funções para geração das chaves utilizadas no cache."""

from uuid import UUID


def _valor_cache(valor: object | None) -> str:
    """Normaliza um valor utilizado na composição de uma chave de cache.

    Args:
        valor: Valor que fará parte da chave.

    Returns:
        Representação textual do valor ou ``none`` quando não informado.
    """
    return "none" if valor is None else str(valor)


def token_enriquecido(
    usuario_id: UUID,
    perfil: str | None = None,
    sistema_id: str | None = None,
) -> str:
    """Retorna a chave de cache do Token Enriquecido.

    Cada combinação de usuário, perfil e sistema representa um contexto
    independente de cache.

    Args:
        usuario_id: Identificador único do usuário.
        perfil: Identificador do perfil selecionado.
        sistema_id: Identificador do sistema selecionado.

    Returns:
        Chave utilizada para armazenar o Token Enriquecido em cache.
    """
    return (
        f"token-enriquecido:"
        f"{usuario_id}:"
        f"{_valor_cache(perfil)}:"
        f"{_valor_cache(sistema_id)}"
    )


def tokens_enriquecidos_usuario(usuario_id: UUID) -> str:
    """Retorna o padrão das chaves de Token Enriquecido de um usuário.

    O padrão permite localizar todas as variações de Token Enriquecido
    pertencentes ao mesmo usuário, independentemente de perfil ou sistema.

    Args:
        usuario_id: Identificador único do usuário.

    Returns:
        Padrão utilizado para localizar os Tokens Enriquecidos do usuário.
    """
    return f"token-enriquecido:{usuario_id}:*"
