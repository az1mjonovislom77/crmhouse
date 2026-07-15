from drf_spectacular.utils import extend_schema
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.base.views_base import BaseUserViewSet
from common.mixins import filter_by_org
from common.permissions import IsAdminOrReadOnly
from common.search import TransliteratedSearchFilter
from user.api.serializers.user_serializers import UserCreateSerializer, UserDetailSerializer
from user.models import User


class UserPagination(PageNumberPagination):
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


@extend_schema(tags=["User"])
class UserViewSet(BaseUserViewSet):
    queryset = User.objects.filter(is_staff=False)
    pagination_class = UserPagination
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [TransliteratedSearchFilter]
    search_fields = ['full_name', 'username', 'phone_number']

    def get_queryset(self):
        return filter_by_org(super().get_queryset(), self.request)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UserDetailSerializer
        return UserCreateSerializer
