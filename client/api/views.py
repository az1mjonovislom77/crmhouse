from drf_spectacular.utils import extend_schema

from client.api.serializers import ClientSerializer
from client.selectors.client_selectors import get_client_queryset
from common.base.pagination_base import DefaultPagination
from common.base.views_base import BaseUserViewSet
from common.mixins import filter_by_org
from common.search import TransliteratedSearchFilter


@extend_schema(tags=["Client"])
class ClientViewSet(BaseUserViewSet):
    serializer_class = ClientSerializer
    pagination_class = DefaultPagination
    filter_backends = [TransliteratedSearchFilter]
    search_fields = ["full_name", "phone_number", "passport", "address"]

    def get_queryset(self):
        return filter_by_org(get_client_queryset(), self.request)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, organization=self.request.user.organization)
