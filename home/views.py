from django.db.models import DecimalField, F, ExpressionWrapper, Value
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from home.models import Home
from home.serializers import HomeGetSerializer, HomeCreateSerializer
from utils.base.views_base import BaseUserViewSet


@extend_schema(tags=['Home'])
class HomeViewSet(BaseUserViewSet):

    def get_queryset(self):
        return (Home.objects.select_related(
            'blocks', 'blocks__projects', 'floor', 'renovation', 'basement', 'booking', 'booking__payment_term')
        .annotate(
            total_price_annotated=ExpressionWrapper(
                Coalesce(F('area') * F('price_per_sqm'), 0) +
                Coalesce(F('basement__price'), 0) +
                Coalesce(F('renovation__price'), 0),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            initial_payment_annotated=ExpressionWrapper(
                (Coalesce(F('area') * F('price_per_sqm'), 0) +
                 Coalesce(F('basement__price'), 0) +
                 Coalesce(F('renovation__price'), 0)) *
                Coalesce(F('booking__down_payment'), 0) / Value(100),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            monthly_payment_annotated=ExpressionWrapper(
                ((Coalesce(F('area') * F('price_per_sqm'), 0) +
                  Coalesce(F('basement__price'), 0) +
                  Coalesce(F('renovation__price'), 0)) -
                 ((Coalesce(F('area') * F('price_per_sqm'), 0) +
                   Coalesce(F('basement__price'), 0) +
                   Coalesce(F('renovation__price'), 0)) *
                  Coalesce(F('booking__down_payment'), 0) / Value(100))) /
                Coalesce(F('booking__payment_term__months'), 1),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )))

    def get_serializer_class(self):
        if self.action == "create":
            return HomeCreateSerializer
        return HomeGetSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['blocks__projects', 'blocks', 'home_status']
