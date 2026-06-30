from drf_spectacular.utils import extend_schema
from rest_framework import filters
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from user.models import RequestLog
from user.api.serializers.log_serializers import RequestLogSerializer
from user.api.views.user_views import UserPagination


class IsAdminOrSuperAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role in ('a', 'sa')


@extend_schema(tags=["RequestLogs"])
class RequestLogListView(ListAPIView):
    serializer_class = RequestLogSerializer
    permission_classes = [IsAdminOrSuperAdmin]
    pagination_class = UserPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'status_code', 'duration_ms']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = RequestLog.objects.select_related('user')
        params = self.request.query_params
        errors = {}

        user_id = params.get('user_id')
        method = params.get('method')
        status_code = params.get('status_code')
        path = params.get('path')
        date_from = params.get('date_from')
        date_to = params.get('date_to')

        if user_id:
            try:
                qs = qs.filter(user_id=int(user_id))
            except ValueError:
                errors['user_id'] = 'Must be an integer.'

        if status_code:
            try:
                qs = qs.filter(status_code=int(status_code))
            except ValueError:
                errors['status_code'] = 'Must be an integer.'

        if errors:
            raise ValidationError(errors)

        if method:
            qs = qs.filter(method=method.upper())
        if path:
            qs = qs.filter(path__icontains=path)
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        return qs
