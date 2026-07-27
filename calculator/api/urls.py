from django.urls import include, path
from rest_framework.routers import DefaultRouter

from calculator.api.views import (
    CalculateView,
    CalculatorConfigView,
    GuaranteeOptionViewSet,
    SubsidyOptionViewSet,
)

router = DefaultRouter()
router.register("guarantee-options", GuaranteeOptionViewSet, basename="guarantee-option")
router.register("subsidy-options", SubsidyOptionViewSet, basename="subsidy-option")

urlpatterns = [
    path("config/", CalculatorConfigView.as_view(), name="calculator-config"),
    path("calculate/", CalculateView.as_view(), name="calculator-calculate"),
    path("", include(router.urls)),
]
