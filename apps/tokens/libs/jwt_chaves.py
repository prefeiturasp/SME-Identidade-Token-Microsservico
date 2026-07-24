"""Utilitários para gerenciamento das chaves utilizadas na assinatura JWT."""

from pathlib import Path
from typing import TypedDict

from django.conf import settings


class ChavePublica(TypedDict):
    """Representa uma chave pública disponível para publicação via JWKS.

    Attributes:
        kid: Identificador único da chave.
        algoritmo: Algoritmo utilizado para assinatura do JWT.
        public_key: Conteúdo da chave pública em formato PEM.
    """

    kid: str
    algoritmo: str
    public_key: str


def _ler_arquivo(caminho: str) -> str:
    """Lê e retorna o conteúdo de um arquivo.

    Args:
        caminho: Caminho do arquivo.

    Returns:
        Conteúdo do arquivo.
    """
    return Path(caminho).read_text(encoding="utf-8")


def _obter_configuracao_str(
    valor: str | None,
    nome: str,
) -> str:
    """Valida uma configuração obrigatória do Django.

    Args:
        valor: Valor configurado.
        nome: Nome da configuração.

    Returns:
        Valor configurado.

    Raises:
        ValueError: Caso a configuração não esteja definida.
    """
    if valor is None:
        raise ValueError(f"A configuração {nome} precisa ser definida.")

    return valor


def obter_chave_privada() -> str:
    """Obtém a chave privada utilizada para assinar JWTs.

    Returns:
        Conteúdo da chave privada em formato PEM.
    """
    caminho = _obter_configuracao_str(
        settings.JWT_ENRIQUECIDO_PRIVATE_KEY_PATH,
        "JWT_ENRIQUECIDO_PRIVATE_KEY_PATH",
    )

    return _ler_arquivo(caminho)


def listar_chaves_publicas() -> list[ChavePublica]:
    """Lista as chaves públicas disponíveis para publicação no JWKS.

    Returns:
        Lista contendo as chaves públicas disponíveis para publicação.
    """
    caminho_publico = _obter_configuracao_str(
        settings.JWT_ENRIQUECIDO_PUBLIC_KEY_PATH,
        "JWT_ENRIQUECIDO_PUBLIC_KEY_PATH",
    )

    kid = _obter_configuracao_str(
        settings.JWT_ENRIQUECIDO_KID,
        "JWT_ENRIQUECIDO_KID",
    )

    algoritmo = _obter_configuracao_str(
        settings.JWT_ENRIQUECIDO_ALGORITMO,
        "JWT_ENRIQUECIDO_ALGORITMO",
    )

    return [
        {
            "kid": kid,
            "algoritmo": algoritmo,
            "public_key": _ler_arquivo(caminho_publico),
        }
    ]
