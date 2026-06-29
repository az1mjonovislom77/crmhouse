from django.urls import path, include
from rest_framework.routers import DefaultRouter
from leads.api.views import LeadViewSet, LeadNotificationViewSet

router = DefaultRouter()
router.register('notifications', LeadNotificationViewSet, basename='lead-notifications')
router.register('', LeadViewSet, basename='leads')

urlpatterns = [
    path('', include(router.urls)),
]
