from rest_framework import serializers
from projects.models import Projects
from utils.models import Blocks


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
