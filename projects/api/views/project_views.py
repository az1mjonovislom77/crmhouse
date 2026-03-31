from drf_spectacular.utils import extend_schema
from projects.api.serializers.project_serializers import ProjectsSerializer, BlocksGetSerializer, \
    BlocksCreateSerializer, FloorsSerializer, \
    RenovationSerializer
from projects.models.project_models import Blocks, Floors, Renovation
from projects.selectors.projects_selectors import get_projects_with_stats
from projects.services.project_service import ProjectService
from common.base.views_base import BaseUserViewSet


@extend_schema(tags=['Projects'])
class ProjectsViewSet(BaseUserViewSet):
    serializer_class = ProjectsSerializer

    def get_queryset(self):
        return get_projects_with_stats()

    def perform_create(self, serializer):
        ProjectService.create_project(serializer.validated_data)

    def perform_update(self, serializer):
        ProjectService.update_project(instance=self.get_object(), validated_data=serializer.validated_data)


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
