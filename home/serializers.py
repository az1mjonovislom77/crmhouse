from rest_framework import serializers
from home.models import FloorPlan, Home


class FloorPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = FloorPlan
        fields = '__all__'


class HomeGetSerializer(serializers.ModelSerializer):
    floorplan = FloorPlanSerializer(many=True, read_only=True)
    block_title = serializers.SerializerMethodField()
    project_title = serializers.SerializerMethodField()
    floor_number = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    initial_payment = serializers.SerializerMethodField()
    monthly_payment = serializers.SerializerMethodField()

    class Meta:
        model = Home
        fields = '__all__'

    def get_block_title(self, obj):
        return obj.blocks.title if obj.blocks else None

    def get_project_title(self, obj):
        return obj.blocks.projects.title if obj.blocks and obj.blocks.projects else None

    def get_floor_number(self, obj):
        return obj.floor.number if obj.floor else None

    def get_total_price(self, obj):
        return obj.total_price

    def get_initial_payment(self, obj):
        return obj.initial_payment

    def get_monthly_payment(self, obj):
        return obj.monthly_payment


class HomeCreateSerializer(serializers.ModelSerializer):
    floorplan = FloorPlanSerializer(many=True)

    class Meta:
        model = Home
        fields = '__all__'
