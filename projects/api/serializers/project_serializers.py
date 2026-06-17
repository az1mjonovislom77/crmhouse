from rest_framework import serializers
from common.base.serializers_base import BaseReadSerializer
from projects.models.project_models import Block, Project, Floors, Renovation


class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = ['title']


class ProjectSerializer(serializers.ModelSerializer):
    blocks = BlockSerializer(many=True, read_only=True)
    homes_count = serializers.IntegerField(read_only=True)
    available_homes = serializers.IntegerField(read_only=True)
    sold_homes = serializers.IntegerField(read_only=True)
    sold_percent = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = '__all__'

    def get_sold_percent(self, obj):
        return round(getattr(obj, 'sold_percent', 0) or 0, 2)


class BlockGetSerializer(serializers.ModelSerializer):
    project_title = serializers.SerializerMethodField()

    class Meta:
        model = Block
        fields = '__all__'

    def get_project_title(self, obj):
        return obj.projects.title if obj.projects else None


class BlockCreateSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Block


class FloorsSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Floors


class RenovationSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Renovation
