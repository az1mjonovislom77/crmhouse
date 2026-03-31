from common.base.serializers_base import BaseReadSerializer
from projects.models.showroom_models import SVG, Showroom
from rest_framework import serializers


class SVGSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = SVG


class ShowroomSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()

    class Meta:
        model = Showroom
        fields = ['id', 'label', 'blocks_number', 'path', 'navigate_to', 'hover_color', 'default_color']

    def get_label(self, obj):
        return obj.blocks.title if obj.blocks else None
