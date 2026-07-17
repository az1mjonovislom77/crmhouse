from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from projects.api.serializers.showroom_serializers import ShowroomImageSerializer, SVGSerializer
from projects.models.showroom_models import SVG, ShowroomImage
from projects.selectors.showroom_selectors import get_showroom_images


@extend_schema(tags=['SVG'])
class SVGView(ListAPIView):
    queryset = SVG.objects.all()
    serializer_class = SVGSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated]


@extend_schema(tags=['Showroom'])
class ShowroomView(ListAPIView):
    serializer_class = ShowroomImageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        if self.request.user.is_staff:
            return get_showroom_images()
        organization = getattr(self.request.user, 'organization', None)
        if organization is None:
            return ShowroomImage.objects.none()
        return get_showroom_images(organization=organization)
