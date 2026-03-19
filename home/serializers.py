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
    total_price = serializers.DecimalField(max_digits=50, decimal_places=2, read_only=True,
                                           source='total_price_annotated')
    initial_payment = serializers.DecimalField(max_digits=50, decimal_places=2, read_only=True,
                                               source='initial_payment_annotated')

    monthly_payment = serializers.DecimalField(max_digits=50, decimal_places=2, read_only=True,
                                               source='monthly_payment_annotated')

    class Meta:
        model = Home
        fields = '__all__'

    def get_block_title(self, obj):
        return obj.blocks.title if obj.blocks else None

    def get_project_title(self, obj):
        return obj.blocks.projects.title if obj.blocks and obj.blocks.projects else None

    def get_floor_number(self, obj):
        return obj.floor.number if obj.floor else None


class HomeCreateSerializer(serializers.ModelSerializer):
    floorplan = FloorPlanSerializer(many=True)

    class Meta:
        model = Home
        fields = '__all__'
