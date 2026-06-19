from django.urls import include, path
from rest_framework.routers import DefaultRouter
from booking.api.views import BookingViewSet, PaymentTermViewSet, PaymentViewSet

router = DefaultRouter()
router.register('payment-term', PaymentTermViewSet, basename='payment-term')
router.register('payments', PaymentViewSet, basename='payment')
router.register('', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),
]
