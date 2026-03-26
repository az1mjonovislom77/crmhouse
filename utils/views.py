from drf_spectacular.utils import extend_schema
from utils.base.views_base import BaseUserViewSet
from utils.models import Blocks, Floors, Renovation
from utils.serializers import BlocksCreateSerializer, BlocksGetSerializer, FloorsSerializer, \
    RenovationSerializer


@extend_schema(tags=['Blocks'])
class BlocksViewSet(BaseUserViewSet):
    queryset = Blocks.objects.select_related('projects')

    def get_serializer_class(self):
        if self.action == 'create':
            return BlocksCreateSerializer
        return BlocksGetSerializer


@extend_schema(tags=['Floors'])
class FloorsViewSet(BaseUserViewSet):
    queryset = Floors.objects.all()
    serializer_class = FloorsSerializer


@extend_schema(tags=['Renovation'])
class RenovationViewSet(BaseUserViewSet):
    queryset = Renovation.objects.all()
    serializer_class = RenovationSerializer
