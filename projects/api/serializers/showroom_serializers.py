from common.base.serializers_base import BaseReadSerializer
from projects.models.showroom_models import SVG, Showroom, ShowroomImage
from rest_framework import serializers


class SVGSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = SVG


class ShowroomImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShowroomImage
        fields = ['id', 'image']


class ShowroomSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    homes_count = serializers.IntegerField(read_only=True)
    available_homes = serializers.IntegerField(read_only=True)
    sold_homes = serializers.IntegerField(read_only=True)
    reserved_homes = serializers.IntegerField(read_only=True)
    project_title = serializers.SerializerMethodField()
    project_id = serializers.SerializerMethodField()
    images = ShowroomImageSerializer(many=True, read_only=True)

    class Meta:
        model = Showroom
        fields = ['id', 'title', 'images', 'label', 'blocks_number', 'path', 'navigate_to', 'hover_color',
                  'default_color', 'homes_count', 'available_homes', 'sold_homes', 'reserved_homes', 'project_title',
                  'project_id']

    def get_label(self, obj):
        return obj.block.title if obj.block else None

    def get_project_title(self, obj):
        return obj.block.projects.title if obj.block and obj.block.projects else None

    def get_project_id(self, obj):
        return obj.block.projects.id if obj.block and obj.block.projects else None
