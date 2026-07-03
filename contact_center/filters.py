from django_filters import rest_framework as filters
from .models import CallRecord


class CallRecordFilter(filters.FilterSet):
    calldate_after = filters.DateTimeFilter(field_name='calldate', lookup_expr='gte')
    calldate_before = filters.DateTimeFilter(field_name='calldate', lookup_expr='lte')
    src = filters.CharFilter(lookup_expr='exact')
    dst = filters.CharFilter(lookup_expr='exact')
    duration_min = filters.NumberFilter(field_name='duration', lookup_expr='gte')

    class Meta:
        model = CallRecord
        fields = [
            'calldate_after', 'calldate_before',
            'src', 'dst', 'disposition', 'duration_min',
        ]
