from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated

from common.base.pagination_base import DefaultPagination
from common.base.views_base import BaseUserViewSet
from common.mixins import filter_by_org
from common.permissions import IsAdminOrReadOnly
from common.search import TransliteratedSearchFilter
from user.api.serializers.user_serializers import UserCreateSerializer, UserDetailSerializer
from user.models import User


@extend_schema(tags=["User"])
class UserViewSet(BaseUserViewSet):
    queryset = User.objects.filter(is_staff=False)
    pagination_class = DefaultPagination
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [TransliteratedSearchFilter]
    search_fields = ['full_name', 'username', 'phone_number']

    def get_queryset(self):
        return filter_by_org(super().get_queryset(), self.request)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UserDetailSerializer
        return UserCreateSerializer
