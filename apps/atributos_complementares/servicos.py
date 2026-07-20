"""Serviços de sincronização de atributos complementares."""

from typing import Any
from uuid import UUID

from django.db import models as django_models

from apps.atributos_complementares.models import AtributoComplementarUsuario
from apps.perfil.models import ProjecaoUsuario


def _identificador_natural(dados: dict[str, Any]) -> dict[str, Any]:
    """Escolhe a chave de upsert a partir do identificador disponível.

    O payload do etl-ms pode trazer RF (servidor), CPF (quase sempre
    presente) ou matrícula (aluno/terceiro). Usa-se a mesma ordem de
    prioridade já adotada em ``validar_e2e`` do etl-ms (RF > CPF >
    matrícula) para decidir qual campo identifica o registro e evitar
    duplicação em reenvios.
    """
    if dados.get("rf"):
        return {"rf": dados["rf"]}
    if dados.get("cpf"):
        return {"cpf": dados["cpf"]}
    return {"matricula": dados["matricula"]}


def _localizar_projecao(dados: dict[str, Any]) -> ProjecaoUsuario | None:
    """Localiza a projeção do usuário por RF ou CPF, se existir.

    O payload do etl-ms não carrega o UUID do Keycloak (chave
    primária de ``ProjecaoUsuario``), então o vínculo é best-effort:
    não bloqueia o upsert quando a projeção ainda não existe, pois a
    carga de perfil e a carga de atributos complementares rodam em
    pipelines independentes, sem ordem garantida entre si.
    """
    filtro = django_models.Q()
    if dados.get("rf"):
        filtro |= django_models.Q(rf=dados["rf"])
    if dados.get("cpf"):
        filtro |= django_models.Q(cpf=dados["cpf"])

    if not filtro:
        return None

    return ProjecaoUsuario.objects.filter(filtro).first()


def sincronizar_lote(
    usuarios: list[dict[str, Any]],
    *,
    id_execucao: UUID | None = None,
) -> dict[str, int]:
    """Cria ou atualiza em lote os atributos complementares recebidos.

    Args:
        usuarios: Lista de dicionários com os atributos complementares
            de cada usuário, já validados pelo serializer de entrada.
        id_execucao: UUID da execução do pipeline ETL de origem.

    Returns:
        Dicionário com a contagem de registros processados, criados
        e atualizados.
    """
    criados = 0
    atualizados = 0

    for dados in usuarios:
        chave = _identificador_natural(dados)
        projecao = _localizar_projecao(dados)

        campos: dict[str, Any] = {
            campo: valor
            for campo, valor in dados.items()
            if campo not in chave
        }
        campos["usuario"] = projecao
        campos["id_execucao"] = id_execucao

        _, foi_criado = AtributoComplementarUsuario.objects.update_or_create(
            defaults=campos,
            **chave,
        )

        if foi_criado:
            criados += 1
        else:
            atualizados += 1

    return {
        "processados": len(usuarios),
        "criados": criados,
        "atualizados": atualizados,
    }
