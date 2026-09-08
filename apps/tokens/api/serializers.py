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
        cpf: CPF do usuário, quando cadastrado no Keycloak.
        rf: Registro funcional do usuário, quando cadastrado no Keycloak.
        perfil: Identificador do perfil selecionado, quando já houver
            um perfil escolhido (ausente no momento do login).
        sistema_id: Identificador do sistema, quando informado.
    """

    kc_user_id = serializers.UUIDField()
    username = serializers.CharField()
    nome = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True)
    ativo = serializers.BooleanField()
    cpf = serializers.CharField(required=False, allow_null=True)
    rf = serializers.CharField(required=False, allow_null=True)
    perfil = serializers.CharField(required=False, allow_null=True)
    sistema_id = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
    )


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
