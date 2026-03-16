from rest_framework import viewsets
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated

User = get_user_model()


class PartialPutMixin:
    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


class BaseUserViewSet(PartialPutMixin, viewsets.ModelViewSet):
    http_method_names = ["get", "post", "put", "delete"]
    permission_classes = [IsAuthenticated]
    pagination_class = None


class ReadWriteSerializerMixin:
    write_actions = {"create", "update", "partial_update"}
    write_serializer = None
    read_serializer = None

    def get_serializer_class(self):
        if self.action in self.write_actions:
            return self.write_serializer or self.serializer_class
        return self.read_serializer or self.serializer_class
