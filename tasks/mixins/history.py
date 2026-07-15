from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer


class HistoryMixin:
    history_serializer_class: type[BaseSerializer] | None = None

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        obj = self.get_object()  # type: ignore[attr-defined]
        history = obj.history.all().order_by('-history_date')

        serializer = self.history_serializer_class(history, many=True)  # type: ignore[misc]
        return Response(serializer.data)
