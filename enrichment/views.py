"""Enrichment API: receives ETL batches, serves /users/{login}/claims."""
from __future__ import annotations

import logging

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.authentication import InternalTokenAuthentication

from .cache import get as cache_get, invalidate as cache_invalidate, set as cache_set
from .claims import build_claims
from .models import ETLBatchLog, UserClaim
from .serializers import (
    ETLBatchLogSerializer,
    PushBatchRequestSerializer,
    UserClaimSerializer,
)

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def push_batch(request):
    """POST /api/v1/etl/push-batch — recebe lote vindo do etl-ms."""
    serializer = PushBatchRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    v = serializer.validated_data
    users = v["users"]

    created = updated = failed = 0
    errors: list[dict] = []

    with transaction.atomic():
        for u in users:
            try:
                claim, was_created = UserClaim.objects.update_or_create(
                    login=u["login"],
                    defaults={
                        "cpf": u.get("cpf", ""),
                        "rf": u.get("rf", ""),
                        "matricula": u.get("matricula", ""),
                        "nome": u.get("nome", ""),
                        "email": u.get("email", ""),
                        "source": u.get("source", ""),
                        "tipo_usuario": u.get("tipo_usuario", ""),
                        "claims": u.get("claims", {}) or {},
                        "execution_id": v.get("execution_id"),
                    },
                )
            except Exception as exc:  # noqa: BLE001
                failed += 1
                errors.append({"login": u.get("login"), "error": str(exc)})
                continue
            cache_invalidate(claim.login)
            if was_created:
                created += 1
            else:
                updated += 1

        ETLBatchLog.objects.create(
            execution_id=v.get("execution_id"),
            users_received=len(users),
            users_created=created,
            users_updated=updated,
            users_failed=failed,
            errors=errors,
        )

    return Response(
        {
            "status": "ok",
            "received": len(users),
            "created": created,
            "updated": updated,
            "failed": failed,
            "errors": errors,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_claims(_request, login: str):
    """GET /api/v1/users/{login}/claims — retorna claims com cache."""
    cached = cache_get(login)
    if cached is not None:
        cached["_cached"] = True
        return Response(cached)

    try:
        claim = UserClaim.objects.get(login=login)
    except UserClaim.DoesNotExist:
        return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)

    payload = build_claims(claim)
    cache_set(login, payload)
    payload["_cached"] = False
    return Response(payload)


class UserClaimViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = [InternalTokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = UserClaim.objects.all()
    serializer_class = UserClaimSerializer
    lookup_field = "login"
    filterset_fields = ["source", "tipo_usuario", "execution_id"]
    search_fields = ["login", "cpf", "rf", "matricula", "nome", "email"]

    @action(detail=True, methods=["post"], url_path="invalidate-cache")
    def invalidate_cache(self, request, login=None):
        cache_invalidate(login)
        return Response({"status": "invalidated", "login": login})


class ETLBatchLogViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = [InternalTokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = ETLBatchLog.objects.all()
    serializer_class = ETLBatchLogSerializer
    filterset_fields = ["execution_id"]
