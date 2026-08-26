"""Serviços de sincronização de atributos complementares."""

from typing import Any
from uuid import UUID

from django.db import models as django_models

from apps.atributos_complementares.models import (
    AtributoComplementarUsuario,
    VinculoAtributoComplementar,
)
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


def _sincronizar_vinculos(
    atributo: AtributoComplementarUsuario, vinculos: list[dict[str, Any]]
) -> None:
    """Sincroniza os vínculos funcionais de um atributo complementar.

    Estratégia "replace": remove vínculos existentes que não vieram no
    payload atual e faz upsert dos que vieram, por
    ``(atributo, tipo_vinculo, codigo_vinculo_origem)`` — mesma chave
    natural da ``UniqueConstraint`` do model, para que reenvios do ETL
    sejam idempotentes (reenviar o mesmo vínculo atualiza o mesmo
    registro; um vínculo que deixou de vir é removido).
    """
    chaves_recebidas = {
        (v["tipo_vinculo"], v["codigo_vinculo_origem"]) for v in vinculos
    }
    for vinculo_existente in atributo.vinculos.all():
        chave_existente = (
            vinculo_existente.tipo_vinculo,
            vinculo_existente.codigo_vinculo_origem,
        )
        if chave_existente not in chaves_recebidas:
            vinculo_existente.delete()

    for dados_vinculo in vinculos:
        VinculoAtributoComplementar.objects.update_or_create(
            atributo=atributo,
            tipo_vinculo=dados_vinculo["tipo_vinculo"],
            codigo_vinculo_origem=dados_vinculo["codigo_vinculo_origem"],
            defaults={
                campo: valor
                for campo, valor in dados_vinculo.items()
                if campo not in ("tipo_vinculo", "codigo_vinculo_origem")
            },
        )


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
        vinculos = dados.pop("vinculos", []) or []

        campos: dict[str, Any] = {
            campo: valor
            for campo, valor in dados.items()
            if campo not in chave
        }
        campos["usuario"] = projecao
        campos["id_execucao"] = id_execucao

        atributo, foi_criado = (
            AtributoComplementarUsuario.objects.update_or_create(
                defaults=campos,
                **chave,
            )
        )
        _sincronizar_vinculos(atributo, vinculos)

        if foi_criado:
            criados += 1
        else:
            atualizados += 1

    return {
        "processados": len(usuarios),
        "criados": criados,
        "atualizados": atualizados,
    }
