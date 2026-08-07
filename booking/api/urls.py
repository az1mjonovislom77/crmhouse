from django.urls import include, path
from rest_framework.routers import DefaultRouter

from booking.api.views import BookingViewSet, CommitmentViewSet, CompanyViewSet, PaymentViewSet

router = DefaultRouter()
router.register("payments", PaymentViewSet, basename="payment")
router.register("commitments", CommitmentViewSet, basename="commitment")
router.register("company", CompanyViewSet, basename="company")
router.register("", BookingViewSet, basename="booking")

urlpatterns = [
    path("", include(router.urls)),
]
