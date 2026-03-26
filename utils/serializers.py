from rest_framework import serializers
from utils.models import Blocks, Floors, Renovation


class BlocksGetSerializer(serializers.ModelSerializer):
    project_title = serializers.SerializerMethodField()

    class Meta:
        model = Blocks
        fields = '__all__'

    def get_project_title(self, obj):
        return obj.projects.title if obj.projects else None


class BlocksCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blocks
        fields = '__all__'


class FloorsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floors
        fields = '__all__'


class RenovationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Renovation
        fields = '__all__'
