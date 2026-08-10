"""Funções para geração das chaves utilizadas no cache."""

from uuid import UUID


def token_enriquecido(usuario_id: UUID) -> str:
    """Retorna a chave de cache do token enriquecido.

    Args:
        usuario_id: Identificador único do usuário.

    Returns:
        Chave utilizada para armazenar o token enriquecido em cache.
    """
    return f"token-enriquecido:{usuario_id}"
