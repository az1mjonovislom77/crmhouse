from common.base.views_base import BaseUserViewSet
from user.models import User
from drf_spectacular.utils import extend_schema
from user.api.serializers.user_serializers import UserCreateSerializer, UserDetailSerializer


@extend_schema(tags=["User"])
class UserViewSet(BaseUserViewSet):
    queryset = User.objects.filter(is_staff=False)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UserDetailSerializer
        return UserCreateSerializer
