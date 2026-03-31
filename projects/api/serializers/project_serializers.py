from rest_framework import serializers
from common.base.serializers_base import BaseReadSerializer
from projects.models.project_models import Blocks, Projects, Floors, Renovation


class BlocksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blocks
        fields = ['title']


class ProjectsSerializer(serializers.ModelSerializer):
    blocks = BlocksSerializer(many=True, read_only=True)
    homes_count = serializers.IntegerField(read_only=True)
    available_homes = serializers.IntegerField(read_only=True)
    sold_homes = serializers.IntegerField(read_only=True)
    sold_percent = serializers.SerializerMethodField()

    class Meta:
        model = Projects
        fields = '__all__'

    def get_sold_percent(self, obj):
        return round(getattr(obj, 'sold_percent', 0) or 0, 2)


class BlocksGetSerializer(serializers.ModelSerializer):
    project_title = serializers.SerializerMethodField()

    class Meta:
        model = Blocks
        fields = '__all__'

    def get_project_title(self, obj):
        return obj.projects.title if obj.projects else None


class BlocksCreateSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Blocks


class FloorsSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Floors


class RenovationSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Renovation
