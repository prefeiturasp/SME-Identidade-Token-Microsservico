from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"admin/claims", views.UserClaimViewSet, basename="userclaim")
router.register(r"admin/etl-logs", views.ETLBatchLogViewSet, basename="etl-log")

urlpatterns = [
    path("etl/push-batch", views.push_batch, name="etl-push-batch"),
    path("users/<str:login>/claims", views.user_claims, name="user-claims"),
    path("", include(router.urls)),
]
