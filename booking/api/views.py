from decimal import Decimal
from django.db.models import Sum, Value, DecimalField, Prefetch, OuterRef, Subquery
from django.db.models.functions import Coalesce
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.exceptions import ValidationError
from booking.models import Booking, PaymentTerm, Payment
from booking.api.serializers import BookingCreateSerializer, BookingGetSerializer, PaymentTermSerializer, \
    PaymentSerializer
from booking.services.booking import delete_booking, create_booking
from common.base.views_base import BaseUserViewSet
from common.mixins import get_user_org, filter_by_org
from common.search import TransliteratedSearchFilter
from home.models import HomeStatusHistory
from home.services.home import HomeService

_client_bookings_qs = (Booking.objects.select_related('home', 'home__renovation', 'payment_term')
.annotate(
    payments_total=Coalesce(Sum('payments__amount'), Value(Decimal('0')), output_field=DecimalField())))

_client_status_history_qs = HomeStatusHistory.objects.select_related('home', 'home__blocks', 'home__floor',
                                                                     'changed_by')


@extend_schema(tags=['PaymentTerm'])
class PaymentTermViewSet(BaseUserViewSet):
    queryset = PaymentTerm.objects.all()
    serializer_class = PaymentTermSerializer


@extend_schema(tags=['Booking'],
               parameters=[OpenApiParameter(name='home_id', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY)])
class BookingViewSet(BaseUserViewSet):
    filter_backends = [TransliteratedSearchFilter]
    search_fields = ['client__full_name', 'client__phone_number', 'booking_no', 'client__from_who']

    def get_queryset(self):
        qs = (Booking.objects.select_related(
            'home', 'home__blocks', 'home__floor', 'home__renovation',
            'company', 'payment_term', 'client',
        ).prefetch_related(
            Prefetch('client__bookings', queryset=_client_bookings_qs),
            Prefetch('client__status_history', queryset=_client_status_history_qs),
        ).annotate(
            payments_total=Coalesce(Sum('payments__amount'), Value(Decimal('0')), output_field=DecimalField())
        ))
        qs = filter_by_org(qs, self.request)
        home_id = self.request.query_params.get('home_id')
        if home_id:
            qs = qs.filter(home_id=home_id)
        return qs

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BookingCreateSerializer
        return BookingGetSerializer

    def perform_create(self, serializer):
        validated_data = dict(serializer.validated_data)
        home_status = validated_data.pop('home_status', None)
        org = get_user_org(self.request)
        if org:
            validated_data['organization'] = org
        booking = create_booking(data=validated_data, user=self.request.user, home_status=home_status)
        serializer.instance = booking

    def perform_update(self, serializer):
        validated_data = serializer.validated_data.copy()
        home_status = validated_data.pop('home_status', None)
        booking = serializer.save()
        if home_status is not None:
            HomeService.change_status(
                home_id=booking.home.id, new_status=home_status, user=self.request.user, client=booking.client)

    def perform_destroy(self, instance):
        delete_booking(booking_id=instance.id, user=self.request.user)


@extend_schema(tags=['Payment'],
               parameters=[OpenApiParameter(name='booking_id', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY)])
class PaymentViewSet(BaseUserViewSet):
    http_method_names = ['get', 'post', 'put', 'delete']
    serializer_class = PaymentSerializer

    def get_queryset(self):
        _booking_total_sq = (
            Payment.objects
            .filter(booking_id=OuterRef('booking_id'))
            .values('booking_id')
            .annotate(total=Sum('amount'))
            .values('total')
        )
        qs = Payment.objects.select_related('booking__home').annotate(
            booking_payments_total=Subquery(_booking_total_sq, output_field=DecimalField()))
        qs = filter_by_org(qs, self.request, field='booking__organization')
        booking_id = self.request.query_params.get('booking_id')
        if booking_id:
            qs = qs.filter(booking_id=booking_id)
        return qs

    def perform_create(self, serializer):
        booking = serializer.validated_data['booking']
        amount = serializer.validated_data['amount']
        remaining = booking.remaining_debt

        if remaining <= 0:
            raise ValidationError({"detail": "Qarz to'liq qoplangan, qo'shimcha to'lov qilib bo'lmaydi."})
        if amount > remaining:
            raise ValidationError(
                {"amount": f"Kiritilgan summa qoldiq qarzdan ({remaining}) ko'p bo'lishi mumkin emas."})
        serializer.save()

    def perform_update(self, serializer):
        if 'amount' in serializer.validated_data:
            instance = serializer.instance
            new_amount = serializer.validated_data['amount']
            old_amount = instance.amount
            booking = instance.booking
            available = booking.remaining_debt + old_amount
            if new_amount > available:
                raise ValidationError(
                    {"amount": f"Kiritilgan summa qoldiq qarzdan ({available}) ko'p bo'lishi mumkin emas."})
        serializer.save()
