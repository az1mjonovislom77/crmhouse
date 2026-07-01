from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from common.base.views_base import BaseUserViewSet, PartialPutMixin
from common.mixins import OrganizationMixin, get_user_org
from common.search import TransliteratedSearchFilter
from tasks.api.serializers.tasks_serializers import CardSerializer, CommentSerializer, ProjectGetSerializer, \
    ProjectCreateSerializer, ProjectUpdateSerializer
from tasks.api.serializers.tasks_history_serializers import ProjectHistorySerializer, CardHistorySerializer, \
    CommentHistorySerializer
from tasks.mixins.audit import AuditMixin
from tasks.mixins.history import HistoryMixin
from tasks.models import Card, Comment, Project
from tasks.permissions import IsProjectMemberOrAdmin


@extend_schema(tags=['Card'])
class CardViewSet(OrganizationMixin, AuditMixin, HistoryMixin, BaseUserViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    history_serializer_class = CardHistorySerializer
    filter_backends = [TransliteratedSearchFilter]
    search_fields = ['title']

    def perform_create(self, serializer):
        org = get_user_org(self.request)
        kwargs = {"created_by": self.request.user}
        if org:
            kwargs["organization"] = org
        serializer.save(**kwargs)


@extend_schema(tags=['Comment'])
class CommentViewSet(OrganizationMixin, AuditMixin, HistoryMixin, BaseUserViewSet):
    queryset = Comment.objects.select_related('user', 'project')
    serializer_class = CommentSerializer
    history_serializer_class = CommentHistorySerializer
    filter_backends = [TransliteratedSearchFilter]
    search_fields = ['text']
    organization_field = 'project__card__organization'

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=['Project'])
class ProjectViewSet(OrganizationMixin, AuditMixin, HistoryMixin, PartialPutMixin, viewsets.ModelViewSet):
    queryset = Project.objects.select_related('card', 'created_by', 'updated_by').prefetch_related(
        'users',
        Prefetch('comments', queryset=Comment.objects.select_related('created_by', 'updated_by')),
    )
    history_serializer_class = ProjectHistorySerializer
    http_method_names = ["get", "post", "put", "delete"]
    permission_classes = [IsAuthenticated, IsProjectMemberOrAdmin]
    pagination_class = None
    filter_backends = [TransliteratedSearchFilter]
    search_fields = ['title', 'description']
    organization_field = 'card__organization'

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProjectUpdateSerializer
        return ProjectGetSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result)
