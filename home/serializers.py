from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from home.models import FloorPlan, Home, HomeStatusHistory


class FloorPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = FloorPlan
        fields = '__all__'


class HomeGetSerializer(serializers.ModelSerializer):
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


class HomeStatusHistorySerializer(serializers.ModelSerializer):
    changed_by = serializers.StringRelatedField()
    home_number = SerializerMethodField()
    home_block = SerializerMethodField()
    home_floor = SerializerMethodField()

    class Meta:
        model = HomeStatusHistory
        fields = ["id", "home", "from_status", "to_status", "changed_by", "changed_at", "home_number", "home_block",
                  "home_floor"]

    def get_home_number(self, obj):
        return obj.home.home_number if obj.home else None

    def get_home_block(self, obj):
        return obj.home.blocks.title if obj.home and obj.home.blocks else None

    def get_home_floor(self, obj):
        return obj.home.floor.number if obj.home and obj.home.floor else None


class HomeDetailGetSerializer(serializers.ModelSerializer):
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
