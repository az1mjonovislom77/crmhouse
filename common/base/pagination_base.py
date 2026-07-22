from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class DefaultPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'

    def get_paginated_response(self, data):
        total = self.page.paginator.count
        limit = self.get_page_size(self.request)
        return Response({
            'page': self.page.number,
            'limit': limit,
            'total': total,
            'total_pages': (total + limit - 1) // limit,
            'data': data,
        })
