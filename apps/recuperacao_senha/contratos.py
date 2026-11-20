"""Dados normalizados fornecidos pelo Gateway ao fluxo de recuperação."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UsuarioIdentidade:
    """Conta consultada pelo Gateway no provedor de identidade."""

    id: str
    login: str
    nome: str
    email: str | None
    ativo: bool
    rf: str | None = None
    cpf: str | None = None
