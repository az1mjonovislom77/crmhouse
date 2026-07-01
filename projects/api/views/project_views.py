from drf_spectacular.utils import extend_schema
from projects.api.serializers.project_serializers import ProjectSerializer, BlockGetSerializer, \
    BlockCreateSerializer, FloorsSerializer, RenovationSerializer
from projects.models.project_models import Block, Floors, Renovation
from projects.selectors.projects_selectors import get_projects_with_stats
from projects.services.project_service import ProjectService
from common.base.views_base import BaseUserViewSet
from common.mixins import get_user_org, filter_by_org
from common.search import TransliteratedSearchFilter


@extend_schema(tags=['Projects'])
class ProjectViewSet(BaseUserViewSet):
    serializer_class = ProjectSerializer
    filter_backends = [TransliteratedSearchFilter]
    search_fields = ['title', 'description']

    def get_queryset(self):
        return filter_by_org(get_projects_with_stats(), self.request)

    def perform_create(self, serializer):
        data = dict(serializer.validated_data)
        org = get_user_org(self.request)
        if org:
            data['organization'] = org
        ProjectService.create_project(data)

    def perform_update(self, serializer):
        ProjectService.update_project(instance=self.get_object(), validated_data=serializer.validated_data)


@extend_schema(tags=['Blocks'])
class BlockViewSet(BaseUserViewSet):
    queryset = Block.objects.select_related('projects')
    filter_backends = [TransliteratedSearchFilter]
    search_fields = ['title', 'projects__title']

    def get_serializer_class(self):
        if self.action == 'create':
            return BlockCreateSerializer
        return BlockGetSerializer


@extend_schema(tags=['Floors'])
class FloorsViewSet(BaseUserViewSet):
    queryset = Floors.objects.all()
    serializer_class = FloorsSerializer


@extend_schema(tags=['Renovation'])
class RenovationViewSet(BaseUserViewSet):
    queryset = Renovation.objects.all()
    serializer_class = RenovationSerializer
    filter_backends = [TransliteratedSearchFilter]
    search_fields = ['title']
