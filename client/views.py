from drf_spectacular.utils import extend_schema
from booking.models import Booking
from client.models import Client
from client.serializers import ClientSerializer
from common.base.views_base import BaseUserViewSet
from home.models import HomeStatusHistory
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.db.models import Prefetch


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
        return Client.objects.prefetch_related(
            Prefetch("bookings",
                     queryset=Booking.objects.select_related("home").prefetch_related(
                         Prefetch("home__status_history",
                                  queryset=HomeStatusHistory.objects.select_related(
                                      "home", "home__blocks", "home__floor", "changed_by"),
                                  to_attr="prefetched_history"))))
