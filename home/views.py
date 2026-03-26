from django.db.models import DecimalField, F, ExpressionWrapper, Value
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from home.models import Home, HomeStatusHistory
from home.serializers import HomeGetSerializer, HomeCreateSerializer, HomeStatusHistorySerializer
from home.services.history import HomeService
from utils.base.views_base import BaseUserViewSet


class HomePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "limit"

    def get_paginated_response(self, data):
        total = self.page.paginator.count
        limit = self.get_page_size(self.request)
        total_pages = (total + limit - 1) // limit

        return Response(
            {
                "page": self.page.number,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "data": data,
            }
        )


@extend_schema(tags=['Home'])
class HomeViewSet(BaseUserViewSet):

    def get_queryset(self):
        return (Home.objects.select_related(
            'blocks', 'blocks__projects', 'floor', 'renovation', 'booking', 'booking__payment_term')
        .annotate(
            total_price_annotated=ExpressionWrapper(
                Coalesce(F('area') * F('price_per_sqm'), 0) +
                Coalesce(F('renovation__price'), 0),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            initial_payment_annotated=ExpressionWrapper(
                (Coalesce(F('area') * F('price_per_sqm'), 0) +
                 Coalesce(F('renovation__price'), 0)) *
                Coalesce(F('booking__down_payment'), 0) / Value(100),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            monthly_payment_annotated=ExpressionWrapper(
                ((Coalesce(F('area') * F('price_per_sqm'), 0) +
                  Coalesce(F('renovation__price'), 0)) -
                 ((Coalesce(F('area') * F('price_per_sqm'), 0) +
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

    def perform_update(self, serializer):
        instance = self.get_object()
        new_status = serializer.validated_data.get("home_status")

        if new_status and new_status != instance.home_status:
            HomeService.change_status(home_id=instance.id, new_status=new_status, user=self.request.user)

        serializer.save()

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        queryset = HomeStatusHistory.objects.select_related("changed_by").filter(home_id=pk).order_by("-changed_at")

        user = request.query_params.get("user")
        if user:
            queryset = queryset.filter(changed_by_id=user)

        serializer = HomeStatusHistorySerializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema(tags=['HomeHistory'])
class HomeHistoryListAPIView(ListAPIView):
    queryset = HomeStatusHistory.objects.select_related("home", "changed_by").order_by("-changed_at")
    serializer_class = HomeStatusHistorySerializer
    pagination_class = HomePagination
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["home", "changed_by", "to_status"]

    def get_queryset(self):
        qs = super().get_queryset()

        date_from = self.request.query_params.get("from")
        date_to = self.request.query_params.get("to")

        if date_from:
            qs = qs.filter(changed_at__gte=date_from)
        if date_to:
            qs = qs.filter(changed_at__lte=date_to)

        return qs
