from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from home.models import Home
from home.serializers import HomeGetSerializer, HomeCreateSerializer
from utils.base.views_base import BaseUserViewSet


@extend_schema(tags=['Home'])
class HomeViewSet(BaseUserViewSet):
    queryset = Home.objects.select_related('blocks', 'floor', 'renovation', 'basement')

    def get_serializer_class(self):
        if self.action == "create":
            return HomeCreateSerializer
        return HomeGetSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['blocks__projects', 'blocks', 'home_status']
