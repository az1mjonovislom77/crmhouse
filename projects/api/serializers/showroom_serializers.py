from common.base.serializers_base import BaseReadSerializer
from projects.models.showroom_models import SVG


class SVGSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = SVG
