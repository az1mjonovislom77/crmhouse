from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from projects.api.serializers.showroom_serializers import SVGSerializer, ShowroomSerializer
from projects.models.showroom_models import SVG, Showroom
from projects.selectors.showroom_selectors import get_blocks_stats


@extend_schema(tags=['SVG'])
class SVGView(ListAPIView):
    queryset = SVG.objects.all()
    serializer_class = SVGSerializer
    pagination_class = None


@extend_schema(tags=['Showroom'])
class ShowroomView(ListAPIView):
    serializer_class = ShowroomSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return get_blocks_stats()
