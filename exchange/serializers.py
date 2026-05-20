from rest_framework import serializers


class ExchangeRequestSerializer(serializers.Serializer):
    subject_token = serializers.CharField(max_length=8192, trim_whitespace=False)
    audience = serializers.CharField(max_length=255)
    requested_token_type = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    requested_subject = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    scope = serializers.CharField(max_length=255, required=False, allow_blank=True)
    client_id = serializers.CharField(max_length=255, required=False, allow_blank=True)
    client_secret = serializers.CharField(
        max_length=512, required=False, allow_blank=True, trim_whitespace=False
    )
