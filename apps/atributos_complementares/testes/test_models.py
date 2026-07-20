"""Testes do models do módulo atributos_complementares."""

from uuid import uuid4

from django.test import TestCase

from apps.atributos_complementares.models import AtributoComplementarUsuario
from apps.perfil.models import ProjecaoUsuario


class TestAtributoComplementarUsuarioModel(TestCase):
    """Testes do model AtributoComplementarUsuario."""

    def setUp(self) -> None:
        """Cria um atributo complementar de usuário."""
        self.atributo = AtributoComplementarUsuario.objects.create(
            rf="1234567",
            cpf="12345678900",
            nome="Usuário Teste",
            tipo_usuario="servidor",
            cargo="Professor",
            situacao="ativo",
            fonte="se1426",
        )

    def test_deve_criar_atributo_complementar(self) -> None:
        """Deve criar um atributo complementar de usuário."""
        assert AtributoComplementarUsuario.objects.count() == 1
        assert self.atributo.rf == "1234567"
        assert self.atributo.cargo == "Professor"
        assert self.atributo.usuario is None

    def test_deve_retornar_rf_no_str(self) -> None:
        """Deve retornar o RF quando disponível."""
        assert str(self.atributo) == "1234567"

    def test_deve_retornar_cpf_no_str_quando_rf_ausente(self) -> None:
        """Deve retornar o CPF quando o RF não estiver disponível."""
        atributo = AtributoComplementarUsuario.objects.create(
            cpf="98765432100",
            nome="Terceiro Teste",
        )

        assert str(atributo) == "98765432100"

    def test_deve_possuir_metadados_corretos(self) -> None:
        """Deve possuir os metadados configurados."""
        meta = AtributoComplementarUsuario._meta

        assert meta.verbose_name == "Atributo complementar de usuário"
        assert (
            meta.verbose_name_plural == "Atributos complementares de usuários"
        )

    def test_deve_relacionar_com_projecao_usuario(self) -> None:
        """Deve relacionar o atributo a uma projeção de usuário."""
        usuario = ProjecaoUsuario.objects.create(
            usuario_id=uuid4(),
            login="usuario.teste",
            rf="1234567",
            nome="Usuário Teste",
            situacao="ATIVO",
        )

        atributo = AtributoComplementarUsuario.objects.create(
            rf="7654321",
            nome="Outro usuário",
            usuario=usuario,
        )

        assert atributo.usuario == usuario
        assert usuario.atributos_complementares.count() == 1

    def test_deve_manter_registro_quando_projecao_removida(self) -> None:
        """Deve preservar o registro quando a projeção é removida."""
        usuario = ProjecaoUsuario.objects.create(
            usuario_id=uuid4(),
            login="usuario.teste2",
            nome="Usuário Teste 2",
            situacao="ATIVO",
        )

        atributo = AtributoComplementarUsuario.objects.create(
            rf="1112223",
            nome="Usuário com vínculo",
            usuario=usuario,
        )

        usuario.delete()
        atributo.refresh_from_db()

        assert atributo.usuario is None
