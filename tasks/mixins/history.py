from typing import Any

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer


class HistoryMixin:
    history_serializer_class: type[BaseSerializer] | None = None
    get_object: Any

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        assert self.history_serializer_class is not None
        obj = self.get_object()
        history = obj.history.all().order_by("-history_date")

        serializer = self.history_serializer_class(history, many=True)
        return Response(serializer.data)
