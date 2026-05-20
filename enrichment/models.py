"""Database models that back the token-ms claim store."""
from __future__ import annotations

import uuid

from django.db import models


class UserClaim(models.Model):
    """Persisted enrichment for a single login (RF, CPF or matrícula)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    login = models.CharField(max_length=64, unique=True, db_index=True)
    cpf = models.CharField(max_length=14, blank=True, db_index=True)
    rf = models.CharField(max_length=20, blank=True, db_index=True)
    matricula = models.CharField(max_length=20, blank=True, db_index=True)
    nome = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    source = models.CharField(max_length=32, blank=True)
    tipo_usuario = models.CharField(max_length=32, blank=True)
    claims = models.JSONField(default=dict, blank=True)
    execution_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["login"]

    def __str__(self) -> str:  # pragma: no cover - admin helper
        return f"UserClaim({self.login})"


class ETLBatchLog(models.Model):
    """Audit row for every ``/etl/push-batch`` call."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution_id = models.UUIDField(null=True, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    users_received = models.IntegerField(default=0)
    users_created = models.IntegerField(default=0)
    users_updated = models.IntegerField(default=0)
    users_failed = models.IntegerField(default=0)
    errors = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-received_at"]

    def __str__(self) -> str:  # pragma: no cover - admin helper
        return f"ETLBatchLog({self.execution_id})"
