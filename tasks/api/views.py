from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from common.base.views_base import BaseUserViewSet, PartialPutMixin
from tasks.api.serializers.tasks_serializers import CardSerializer, CommentSerializer, ProjectGetSerializer, \
    ProjectCreateSerializer, ProjectUpdateSerializer
from tasks.api.serializers.tasks_history_serializers import ProjectHistorySerializer, CardHistorySerializer, \
    CommentHistorySerializer
from tasks.mixins.audit import AuditMixin
from tasks.mixins.history import HistoryMixin
from tasks.models import Card, Comment, Project
from tasks.permissions import IsProjectMemberOrAdmin
from rest_framework.response import Response


@extend_schema(tags=['Card'])
class CardViewSet(AuditMixin, HistoryMixin, BaseUserViewSet, ):
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    history_serializer_class = CardHistorySerializer


@extend_schema(tags=['Comment'])
class CommentViewSet(AuditMixin, HistoryMixin, BaseUserViewSet):
    queryset = Comment.objects.select_related('user', 'project')
    serializer_class = CommentSerializer
    history_serializer_class = CommentHistorySerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=['Project'])
class ProjectViewSet(AuditMixin, HistoryMixin, PartialPutMixin, viewsets.ModelViewSet):
    queryset = Project.objects.select_related('card').prefetch_related('users', 'comments')
    history_serializer_class = ProjectHistorySerializer
    http_method_names = ["get", "post", "put", "delete"]
    permission_classes = [IsAuthenticated, IsProjectMemberOrAdmin]
    pagination_class = None

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProjectUpdateSerializer
        return ProjectGetSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        result = serializer.save()

        return Response(result)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        result = serializer.save()

        return Response(result)
