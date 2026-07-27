from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated

from common.base.views_base import BaseUserViewSet
from common.mixins import filter_by_org
from common.permissions import IsAdminOrReadOnly
from common.search import TransliteratedSearchFilter
from projects.api.serializers.project_serializers import (
    BlockCreateSerializer,
    BlockGetSerializer,
    FloorsSerializer,
    ProjectSerializer,
    RenovationSerializer,
)
from projects.models.project_models import Block, Floors, Renovation
from projects.selectors.projects_selectors import get_projects_with_stats
from projects.services.project_service import ProjectService


@extend_schema(tags=["Projects"])
class ProjectViewSet(BaseUserViewSet):
    serializer_class = ProjectSerializer
    filter_backends = [TransliteratedSearchFilter]
    search_fields = ["title", "description"]

    def get_queryset(self):
        return filter_by_org(get_projects_with_stats(), self.request, field="organization")

    def perform_create(self, serializer):
        validated_data = dict(serializer.validated_data)
        validated_data["user"] = self.request.user
        validated_data["organization"] = getattr(self.request.user, "organization", None)
        serializer.instance = ProjectService.create_project(validated_data)

    def perform_update(self, serializer):
        validated_data = dict(serializer.validated_data)
        validated_data.pop("user", None)
        ProjectService.update_project(instance=self.get_object(), validated_data=validated_data)


@extend_schema(tags=["Blocks"])
class BlockViewSet(BaseUserViewSet):
    filter_backends = [TransliteratedSearchFilter]
    search_fields = ["title", "projects__title"]

    def get_queryset(self):
        qs = Block.objects.select_related("projects")
        return filter_by_org(qs, self.request, field="projects__organization")

    def get_serializer_class(self):
        if self.action == "create":
            return BlockCreateSerializer
        return BlockGetSerializer


@extend_schema(tags=["Floors"])
class FloorsViewSet(BaseUserViewSet):
    queryset = Floors.objects.all()
    serializer_class = FloorsSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


@extend_schema(tags=["Renovation"])
class RenovationViewSet(BaseUserViewSet):
    queryset = Renovation.objects.all()
    serializer_class = RenovationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [TransliteratedSearchFilter]
    search_fields = ["title"]
