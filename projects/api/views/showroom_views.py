from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from projects.api.serializers.showroom_serializers import SVGSerializer, ShowroomSerializer
from projects.models.showroom_models import SVG, Showroom


@extend_schema(tags=['SVG'])
class SVGView(ListAPIView):
    queryset = SVG.objects.all()
    serializer_class = SVGSerializer
    pagination_class = None


@extend_schema(tags=['Showroom'])
class ShowroomView(ListAPIView):
    queryset = Showroom.objects.all()
    serializer_class = ShowroomSerializer
    pagination_class = None
