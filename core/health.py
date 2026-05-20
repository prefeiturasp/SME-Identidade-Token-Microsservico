"""Health-check views for token-ms (public, no auth)."""
from django.http import JsonResponse


def liveness(_request):
    return JsonResponse({"status": "ok", "service": "token-ms"})


def readiness(_request):
    return JsonResponse({"status": "ready", "service": "token-ms"})
