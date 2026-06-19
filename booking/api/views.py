from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.exceptions import ValidationError
from booking.models import Booking, PaymentTerm, Payment
from booking.api.serializers import BookingCreateSerializer, BookingGetSerializer, PaymentTermSerializer, PaymentSerializer
from booking.services.booking import delete_booking, create_booking
from common.base.views_base import BaseUserViewSet
from home.services.home import HomeService


@extend_schema(tags=['PaymentTerm'])
class PaymentTermViewSet(BaseUserViewSet):
    queryset = PaymentTerm.objects.all()
    serializer_class = PaymentTermSerializer


@extend_schema(tags=['Booking'],
               parameters=[OpenApiParameter(name='home_id', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY)])
class BookingViewSet(BaseUserViewSet):
    queryset = Booking.objects.select_related('home', 'home__blocks', 'home__floor', 'company', 'payment_term',
                                              'client', 'home__renovation')

    def get_queryset(self):
        queryset = super().get_queryset()
        home_id = self.request.query_params.get('home_id')

        if home_id:
            queryset = queryset.filter(home_id=home_id)

        return queryset

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BookingCreateSerializer
        return BookingGetSerializer

    def perform_create(self, serializer):
        validated_data = serializer.validated_data.copy()

        home_status = validated_data.pop('home_status', None)
        booking = create_booking(data=validated_data, user=self.request.user, home_status=home_status)

        serializer.instance = booking

    def perform_update(self, serializer):
        validated_data = serializer.validated_data.copy()

        home_status = validated_data.pop('home_status', None)

        booking = serializer.save()

        if home_status is not None:
            HomeService.change_status(
                home_id=booking.home.id,
                new_status=home_status,
                user=self.request.user,
                client=booking.client
            )

    def perform_destroy(self, instance):
        delete_booking(booking_id=instance.id, user=self.request.user)


@extend_schema(tags=['Payment'],
               parameters=[OpenApiParameter(name='booking_id', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY)])
class PaymentViewSet(BaseUserViewSet):
    http_method_names = ['get', 'post']
    queryset = Payment.objects.select_related('booking__home')
    serializer_class = PaymentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        booking_id = self.request.query_params.get('booking_id')
        if booking_id:
            queryset = queryset.filter(booking_id=booking_id)
        return queryset

    def perform_create(self, serializer):
        booking = serializer.validated_data['booking']
        amount = serializer.validated_data['amount']
        remaining = booking.remaining_debt

        if remaining <= 0:
            raise ValidationError({"detail": "Qarz to'liq qoplangan, qo'shimcha to'lov qilib bo'lmaydi."})

        if amount > remaining:
            raise ValidationError({"amount": f"Kiritilgan summa qoldiq qarzdan ({remaining}) ko'p bo'lishi mumkin emas."})

        serializer.save()
