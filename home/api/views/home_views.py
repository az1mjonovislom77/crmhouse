from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from home.api.serializers.home_serializers import HomeGetSerializer, HomeDetailGetSerializer, HomeCreateSerializer, \
    HomeStatusHistorySerializer
from home.models import HomeStatusHistory
from home.selectors.history_selectors import get_home_history
from home.selectors.home_selectors import get_homes_with_finance
from home.services.home import HomeService
from common.base.views_base import BaseUserViewSet


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
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['blocks__projects', 'blocks', 'home_status']

    def get_queryset(self):
        return get_homes_with_finance()

    def get_serializer_class(self):
        if self.action == "create":
            return HomeCreateSerializer
        elif self.action == "retrieve":
            return HomeDetailGetSerializer
        return HomeGetSerializer

    def perform_create(self, serializer):
        HomeService.create_home(serializer.validated_data)

    def perform_update(self, serializer):
        instance = self.get_object()

        new_status = serializer.validated_data.get("home_status")

        if new_status and new_status != instance.home_status:
            HomeService.change_status(home_id=instance.id, new_status=new_status, user=self.request.user)

        HomeService.update_home(instance, serializer.validated_data)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        user = request.query_params.get("user")

        queryset = get_home_history(home_id=pk, user_id=user)

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
