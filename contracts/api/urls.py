from django.urls import include, path
from rest_framework.routers import DefaultRouter

from contracts.api.views import ContractTemplateViewSet, ContractViewSet

router = DefaultRouter()
router.register("templates", ContractTemplateViewSet, basename="contract-template")
router.register("", ContractViewSet, basename="contract")

urlpatterns = [
    path("", include(router.urls)),
]
