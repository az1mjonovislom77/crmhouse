from drf_spectacular.utils import extend_schema
from client.models import Client
from client.serializers import ClientSerializer
from utils.base.views_base import BaseUserViewSet


@extend_schema(tags=['Client'])
class ClientViewSet(BaseUserViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
