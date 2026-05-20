from rest_framework import serializers

from .models import ETLBatchLog, UserClaim


class PushBatchUserSerializer(serializers.Serializer):
    login = serializers.CharField(max_length=64, required=False, allow_blank=True)
    cpf = serializers.CharField(max_length=14, required=False, allow_blank=True)
    rf = serializers.CharField(max_length=20, required=False, allow_blank=True)
    matricula = serializers.CharField(max_length=20, required=False, allow_blank=True)
    nome = serializers.CharField(max_length=255, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    source = serializers.CharField(max_length=32, required=False, allow_blank=True)
    tipo_usuario = serializers.CharField(
        max_length=32, required=False, allow_blank=True
    )
    claims = serializers.DictField(required=False)

    def validate(self, attrs):
        login = (
            attrs.get("login")
            or attrs.get("rf")
            or attrs.get("cpf")
            or attrs.get("matricula")
        )
        if not login:
            raise serializers.ValidationError(
                "Pelo menos um identificador (login, rf, cpf, matricula) é obrigatório."
            )
        attrs["login"] = login
        return attrs


class PushBatchRequestSerializer(serializers.Serializer):
    execution_id = serializers.UUIDField(required=False, allow_null=True)
    users = PushBatchUserSerializer(many=True)


class UserClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserClaim
        fields = "__all__"


class ETLBatchLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ETLBatchLog
        fields = "__all__"
