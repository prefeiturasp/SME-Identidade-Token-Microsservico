"""Serializers utilizados na validação de tokens JWT."""

from rest_framework import serializers


class ValidarTokenRequestSerializer(serializers.Serializer):
    """Representa o payload da requisição de validação de um JWT.

    Attributes:
        token: Token JWT a ser validado.
    """

    token = serializers.CharField()


class ValidarTokenResponseSerializer(serializers.Serializer):
    """Representa o resultado da validação de um JWT.

    Attributes:
        valido: Indica se o token é válido.
        expirado: Indica se o token está expirado.
        claims: Claims extraídas do token, quando disponíveis.
    """

    valido = serializers.BooleanField()
    expirado = serializers.BooleanField()
    claims = serializers.DictField(required=False)


class TokenEnriquecidoRequestSerializer(serializers.Serializer):
    """Representa os dados utilizados para geração do JWT enriquecido.

    Attributes:
        kc_user_id: Identificador do usuário no Keycloak.
        username: Usuário/login da conta.
        nome: Nome completo do usuário.
        email: E-mail do usuário.
        ativo: Indica se a conta está ativa.
        cpf: CPF do usuário.
        rf: Registro funcional do usuário.
        perfil: Identificador do perfil selecionado.
    """

    kc_user_id = serializers.UUIDField()
    username = serializers.CharField()
    nome = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True)
    ativo = serializers.BooleanField()
    cpf = serializers.CharField()
    rf = serializers.CharField()
    perfil = serializers.CharField()


class TokenEnriquecidoResponseSerializer(serializers.Serializer):
    """Representa a resposta da geração do token enriquecido.

    Attributes:
        token: JWT enriquecido gerado e assinado pelo Token-MS.
        data_expiracao: Data e hora em que o token enriquecido expira.
        permissoes: Lista de permissões associadas ao usuário.
    """

    token = serializers.CharField()
    data_expiracao = serializers.DateTimeField()
    permissoes = serializers.ListField(
        child=serializers.DictField(),
    )
