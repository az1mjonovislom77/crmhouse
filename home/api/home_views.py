from django.db import transaction
from django.utils.dateparse import parse_date
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from home.api.home_serializers import HomeGetSerializer, HomeDetailGetSerializer, HomeCreateSerializer, \
    HomeStatusHistorySerializer
from home.models import HomeStatusHistory
from home.selectors.history_selectors import get_home_history
from home.selectors.home_selectors import get_homes_with_finance
from home.services.home import HomeService
from common.base.views_base import BaseUserViewSet
from common.mixins import filter_by_org


class HomePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "limit"
    max_page_size = 100

    def get_paginated_response(self, data):
        total = self.page.paginator.count
        limit = self.get_page_size(self.request)
        total_pages = (total + limit - 1) // limit
        return Response({
            "page": self.page.number,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "data": data,
        })


@extend_schema(tags=['Home'])
class HomeViewSet(BaseUserViewSet):
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['blocks__projects', 'blocks', 'home_status']

    def get_queryset(self):
        qs = get_homes_with_finance()
        return filter_by_org(qs, self.request, field='organization')

    def get_serializer_class(self):
        if self.action == "create":
            return HomeCreateSerializer
        elif self.action == "retrieve":
            return HomeDetailGetSerializer
        return HomeGetSerializer

    def perform_create(self, serializer):
        data = serializer.validated_data
        data['organization'] = getattr(self.request.user, 'organization', None)
        serializer.instance = HomeService.create_home(data)

    def perform_update(self, serializer):
        instance = self.get_object()
        new_status = serializer.validated_data.get("home_status")
        with transaction.atomic():
            if new_status and new_status != instance.home_status:
                HomeService.change_status(home_id=instance.id, new_status=new_status, user=self.request.user)
            HomeService.update_home(instance, serializer.validated_data)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        home = self.get_object()
        user = request.query_params.get("user")
        queryset = get_home_history(home_id=home.pk, user_id=user)
        serializer = HomeStatusHistorySerializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema(tags=['HomeHistory'])
class HomeHistoryListAPIView(ListAPIView):
    serializer_class = HomeStatusHistorySerializer
    pagination_class = HomePagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["home", "changed_by", "to_status"]

    def get_queryset(self):
        qs = HomeStatusHistory.objects.select_related(
            "home", "home__blocks", "home__floor", "changed_by"
        ).order_by("-changed_at")
        qs = filter_by_org(qs, self.request, field='home__organization')
        date_from = self.request.query_params.get("from")
        date_to = self.request.query_params.get("to")
        if date_from:
            parsed = parse_date(date_from)
            if parsed is None:
                raise ValidationError({"from": "Noto'g'ri sana formati, YYYY-MM-DD bo'lishi kerak."})
            qs = qs.filter(changed_at__date__gte=parsed)
        if date_to:
            parsed = parse_date(date_to)
            if parsed is None:
                raise ValidationError({"to": "Noto'g'ri sana formati, YYYY-MM-DD bo'lishi kerak."})
            qs = qs.filter(changed_at__date__lte=parsed)
        return qs
