"""Testes dos serviços de atributos complementares."""

from typing import Any
from uuid import uuid4

from django.test import TestCase

from apps.atributos_complementares.models import (
    AtributoComplementarUsuario,
    VinculoAtributoComplementar,
)
from apps.atributos_complementares.servicos import (
    _identificador_natural,
    _localizar_projecao,
    sincronizar_lote,
)
from apps.perfil.models import ProjecaoUsuario


class TestIdentificadorNatural(TestCase):
    """Testes da definição da chave natural do atributo complementar."""

    def test_deve_priorizar_rf(self) -> None:
        """Deve usar RF quando estiver disponível."""
        dados = {
            "rf": "1234567",
            "cpf": "12345678900",
            "matricula": "MAT123",
        }

        assert _identificador_natural(dados) == {
            "rf": "1234567",
        }

    def test_deve_usar_cpf_quando_rf_nao_existir(self) -> None:
        """Deve usar CPF quando RF não estiver disponível."""
        dados = {
            "rf": None,
            "cpf": "12345678900",
            "matricula": "MAT123",
        }

        assert _identificador_natural(dados) == {
            "cpf": "12345678900",
        }

    def test_deve_usar_matricula_quando_rf_e_cpf_nao_existirem(self) -> None:
        """Deve usar matrícula quando RF e CPF não estiverem disponíveis."""
        dados = {
            "rf": None,
            "cpf": None,
            "matricula": "MAT123",
        }

        assert _identificador_natural(dados) == {
            "matricula": "MAT123",
        }


class TestLocalizarProjecao(TestCase):
    """Testes da localização da projeção de usuário."""

    def test_deve_localizar_projecao_por_rf(self) -> None:
        """Deve localizar a projeção pelo RF."""
        usuario = ProjecaoUsuario.objects.create(
            usuario_id=uuid4(),
            login="usuario.rf",
            rf="1234567",
            nome="Usuário RF",
            situacao="ATIVO",
        )

        resultado = _localizar_projecao(
            {
                "rf": "1234567",
                "cpf": None,
            }
        )

        assert resultado == usuario

    def test_deve_localizar_projecao_por_cpf(self) -> None:
        """Deve localizar a projeção pelo CPF."""
        usuario = ProjecaoUsuario.objects.create(
            usuario_id=uuid4(),
            login="usuario.cpf",
            cpf="12345678900",
            nome="Usuário CPF",
            situacao="ATIVO",
        )

        resultado = _localizar_projecao(
            {
                "rf": None,
                "cpf": "12345678900",
            }
        )

        assert resultado == usuario

    def test_deve_retornar_none_sem_rf_e_cpf(self) -> None:
        """Deve retornar None quando não houver RF nem CPF."""
        resultado = _localizar_projecao(
            {
                "rf": None,
                "cpf": None,
                "matricula": "MAT123",
            }
        )

        assert resultado is None

    def test_deve_retornar_none_quando_projecao_nao_existir(self) -> None:
        """Deve retornar None quando não houver projeção correspondente."""
        resultado = _localizar_projecao(
            {
                "rf": "9999999",
                "cpf": "99999999999",
            }
        )

        assert resultado is None


class TestSincronizarLote(TestCase):
    """Testes da sincronização de atributos complementares."""

    def test_deve_criar_atributo_complementar(self) -> None:
        """Deve criar atributo complementar quando ainda não existir."""
        id_execucao = uuid4()

        usuarios: list[dict[str, Any]] = [
            {
                "rf": "1234567",
                "cpf": "12345678900",
                "matricula": None,
                "nome": "Usuário Teste",
                "email": "usuario@teste.com",
                "tipo_usuario": "servidor",
                "cargo": "Professor",
                "funcao": None,
                "unidade": "EMEF Teste",
                "unidade_codigo": "001",
                "dre": "DRE01",
                "ue": None,
                "cod_escola": None,
                "turma": None,
                "tipo_acesso": "servidor",
                "situacao": "ativo",
                "fonte": "se1426",
                "vinculos": [],
            }
        ]

        resultado = sincronizar_lote(
            usuarios,
            id_execucao=id_execucao,
        )

        assert resultado == {
            "processados": 1,
            "criados": 1,
            "atualizados": 0,
        }

        atributo = AtributoComplementarUsuario.objects.get(
            rf="1234567",
        )

        assert atributo.nome == "Usuário Teste"
        assert atributo.cargo == "Professor"
        assert atributo.id_execucao == id_execucao

    def test_deve_atualizar_atributo_complementar_existente(self) -> None:
        """Deve atualizar atributo existente usando sua chave natural."""
        atributo = AtributoComplementarUsuario.objects.create(
            rf="1234567",
            nome="Nome Antigo",
            cargo="Cargo Antigo",
        )

        usuarios = [
            {
                "rf": "1234567",
                "nome": "Nome Atualizado",
                "cargo": "Professor",
                "vinculos": [],
            }
        ]

        resultado = sincronizar_lote(usuarios)

        assert resultado == {
            "processados": 1,
            "criados": 0,
            "atualizados": 1,
        }

        atributo.refresh_from_db()

        assert atributo.nome == "Nome Atualizado"
        assert atributo.cargo == "Professor"
        assert AtributoComplementarUsuario.objects.count() == 1

    def test_deve_relacionar_atributo_com_projecao_por_rf(self) -> None:
        """Deve vincular atributo à projeção encontrada pelo RF."""
        usuario = ProjecaoUsuario.objects.create(
            usuario_id=uuid4(),
            login="usuario.teste",
            rf="1234567",
            nome="Usuário Teste",
            situacao="ATIVO",
        )

        usuarios = [
            {
                "rf": "1234567",
                "nome": "Usuário Teste",
                "vinculos": [],
            }
        ]

        sincronizar_lote(usuarios)

        atributo = AtributoComplementarUsuario.objects.get(
            rf="1234567",
        )

        assert atributo.usuario == usuario

    def test_deve_criar_atributo_sem_projecao_relacionada(self) -> None:
        """Deve permitir criação mesmo sem projeção existente."""
        usuarios = [
            {
                "matricula": "MAT123",
                "nome": "Aluno Teste",
                "vinculos": [],
            }
        ]

        resultado = sincronizar_lote(usuarios)

        assert resultado == {
            "processados": 1,
            "criados": 1,
            "atualizados": 0,
        }

        atributo = AtributoComplementarUsuario.objects.get(
            matricula="MAT123",
        )

        assert atributo.usuario is None

    def test_deve_criar_vinculo_recebido_no_payload(self) -> None:
        """Deve criar vínculo funcional recebido na sincronização."""
        usuarios = [
            {
                "rf": "1234567",
                "nome": "Usuário Teste",
                "vinculos": [
                    {
                        "tipo_vinculo": "cargo",
                        "codigo_vinculo_origem": "123",
                        "cargo_codigo": "PROF",
                        "cargo_nome": "Professor",
                        "unidade_codigo": "001",
                        "unidade_nome": "EMEF Teste",
                        "dre_codigo": "DRE01",
                        "situacao": "ATIVO",
                        "data_inicio": "2026-01-01",
                        "vigente": True,
                    }
                ],
            }
        ]

        resultado = sincronizar_lote(usuarios)

        assert resultado == {
            "processados": 1,
            "criados": 1,
            "atualizados": 0,
        }

        atributo = AtributoComplementarUsuario.objects.get(
            rf="1234567",
        )

        assert atributo.vinculos.count() == 1

        vinculo = atributo.vinculos.get()

        assert vinculo.tipo_vinculo == "cargo"
        assert vinculo.codigo_vinculo_origem == "123"
        assert vinculo.cargo_codigo == "PROF"
        assert vinculo.cargo_nome == "Professor"
        assert vinculo.unidade_codigo == "001"
        assert vinculo.unidade_nome == "EMEF Teste"
        assert vinculo.dre_codigo == "DRE01"
        assert vinculo.situacao == "ATIVO"
        assert vinculo.data_inicio == "2026-01-01"
        assert vinculo.vigente is True

    def test_deve_atualizar_vinculo_existente_sem_duplicar(self) -> None:
        """Deve atualizar vínculo existente mantendo a mesma chave natural."""
        atributo = AtributoComplementarUsuario.objects.create(
            rf="1234567",
            nome="Usuário Teste",
        )

        vinculo = VinculoAtributoComplementar.objects.create(
            atributo=atributo,
            tipo_vinculo="cargo",
            codigo_vinculo_origem="123",
            cargo_nome="Cargo Antigo",
            vigente=True,
        )

        usuarios = [
            {
                "rf": "1234567",
                "nome": "Usuário Teste",
                "vinculos": [
                    {
                        "tipo_vinculo": "cargo",
                        "codigo_vinculo_origem": "123",
                        "cargo_nome": "Professor Atualizado",
                        "vigente": True,
                    }
                ],
            }
        ]

        resultado = sincronizar_lote(usuarios)

        assert resultado == {
            "processados": 1,
            "criados": 0,
            "atualizados": 1,
        }

        vinculo.refresh_from_db()

        assert atributo.vinculos.count() == 1
        assert vinculo.cargo_nome == "Professor Atualizado"

    def test_deve_remover_vinculo_ausente_no_novo_payload(self) -> None:
        """Deve remover vínculo antigo ausente na nova sincronização."""
        atributo = AtributoComplementarUsuario.objects.create(
            rf="1234567",
            nome="Usuário Teste",
        )

        VinculoAtributoComplementar.objects.create(
            atributo=atributo,
            tipo_vinculo="cargo",
            codigo_vinculo_origem="ANTIGO",
            cargo_nome="Cargo Antigo",
        )

        usuarios = [
            {
                "rf": "1234567",
                "nome": "Usuário Teste",
                "vinculos": [],
            }
        ]

        resultado = sincronizar_lote(usuarios)

        assert resultado == {
            "processados": 1,
            "criados": 0,
            "atualizados": 1,
        }

        assert atributo.vinculos.count() == 0

    def test_deve_manter_vinculo_recebido_e_remover_o_ausente(self) -> None:
        """Deve aplicar estratégia replace aos vínculos funcionais."""
        atributo = AtributoComplementarUsuario.objects.create(
            rf="1234567",
            nome="Usuário Teste",
        )

        vinculo_mantido = VinculoAtributoComplementar.objects.create(
            atributo=atributo,
            tipo_vinculo="cargo",
            codigo_vinculo_origem="MANTER",
            cargo_nome="Cargo Antigo",
        )

        VinculoAtributoComplementar.objects.create(
            atributo=atributo,
            tipo_vinculo="funcao",
            codigo_vinculo_origem="REMOVER",
            cargo_nome="Função Antiga",
        )

        usuarios = [
            {
                "rf": "1234567",
                "nome": "Usuário Teste",
                "vinculos": [
                    {
                        "tipo_vinculo": "cargo",
                        "codigo_vinculo_origem": "MANTER",
                        "cargo_nome": "Cargo Atualizado",
                        "vigente": True,
                    },
                    {
                        "tipo_vinculo": "cargo",
                        "codigo_vinculo_origem": "NOVO",
                        "cargo_nome": "Novo Cargo",
                        "vigente": True,
                    },
                ],
            }
        ]

        sincronizar_lote(usuarios)

        vinculo_mantido.refresh_from_db()

        assert vinculo_mantido.cargo_nome == "Cargo Atualizado"

        assert not atributo.vinculos.filter(
            codigo_vinculo_origem="REMOVER",
        ).exists()

        assert atributo.vinculos.filter(
            codigo_vinculo_origem="NOVO",
        ).exists()

        assert atributo.vinculos.count() == 2

    def test_deve_tratar_vinculos_nulos_como_lista_vazia(self) -> None:
        """Deve tratar vínculos nulos como uma lista vazia."""
        atributo = AtributoComplementarUsuario.objects.create(
            rf="1234567",
            nome="Usuário Teste",
        )

        VinculoAtributoComplementar.objects.create(
            atributo=atributo,
            tipo_vinculo="cargo",
            codigo_vinculo_origem="ANTIGO",
        )

        usuarios = [
            {
                "rf": "1234567",
                "nome": "Usuário Teste",
                "vinculos": None,
            }
        ]

        resultado = sincronizar_lote(usuarios)

        assert resultado == {
            "processados": 1,
            "criados": 0,
            "atualizados": 1,
        }

        assert atributo.vinculos.count() == 0
