from drf_spectacular.utils import extend_schema
from rest_framework import status, permissions
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend

from contact_center.filters import CallRecordFilter
from contact_center.models import CallRecord
from contact_center.serializers import CRSerializer
from contact_center.tasks import sync_cdr_data


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'results': data,
        })


@extend_schema(
    tags=['CDR'],
    summary="CDR ma'lumotlari ro'yxati (paginated + filtered)",
    description="Sana, src, dst, disposition bo'yicha filter qilish mumkin.",
)
class CDRListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CRSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = CallRecordFilter
    search_fields = ['clid', 'uniqueid', 'src', 'dst']
    queryset = CallRecord.objects.all().order_by('-calldate')

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            sync_cdr_data.delay()
            return Response({
                'message': "Ma'lumotlar yangilanmoqda, 10-60 soniya ichida qayta so'rang",
                'count': 0,
                'results': [],
            }, status=status.HTTP_200_OK)
        return super().get(request, *args, **kwargs)
