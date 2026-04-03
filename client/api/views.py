from drf_spectacular.utils import extend_schema
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from client.selectors.client_selectors import get_client_queryset
from common.base.views_base import BaseUserViewSet
from client.api.serializers import ClientSerializer


class ClientPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "limit"

    def get_paginated_response(self, data):
        total = self.page.paginator.count
        limit = self.get_page_size(self.request)
        total_pages = (total + limit - 1) // limit

        return Response(
            {
                "page": self.page.number,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "data": data,
            }
        )


@extend_schema(tags=['Client'])
class ClientViewSet(BaseUserViewSet):
    serializer_class = ClientSerializer
    pagination_class = ClientPagination

    def get_queryset(self):
        return get_client_queryset()
