from django.urls import include, path
from rest_framework.routers import DefaultRouter

from leads.api.views import LeadNotificationViewSet, LeadViewSet

router = DefaultRouter()
router.register("notifications", LeadNotificationViewSet, basename="lead-notifications")
router.register("", LeadViewSet, basename="leads")

urlpatterns = [
    path("", include(router.urls)),
]
