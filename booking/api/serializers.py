from rest_framework import serializers
from booking.models import Booking, PaymentTerm, Company
from booking.services.booking import create_booking
from client.api.serializers import ClientSerializer
from common.base.serializers_base import BaseReadSerializer
from home.models import Home


class PaymentTermSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = PaymentTerm


class CompanySerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Company


class BookingGetSerializer(serializers.ModelSerializer):
    home_number = serializers.SerializerMethodField()
    payment_term_months = serializers.SerializerMethodField()
    client = ClientSerializer(read_only=True)
    home_status = serializers.ChoiceField(choices=Home.HomeStatus.choices, write_only=True, required=False)
    block_title = serializers.SerializerMethodField()
    floor_number = serializers.SerializerMethodField()
    total_area = serializers.SerializerMethodField()
    rooms_number = serializers.SerializerMethodField()
    company = CompanySerializer(read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'

    def get_home_number(self, obj):
        return obj.home.home_number if obj.home else None

    def get_payment_term_months(self, obj):
        return obj.payment_term.months if obj.payment_term else None

    def get_block_title(self, obj):
        return obj.home.blocks.title if obj.home.blocks else None

    def get_floor_number(self, obj):
        return obj.home.floor.number if obj.home.floor else None

    def get_rooms_number(self, obj):
        return obj.home.rooms.number if obj.home.rooms else None

    def get_total_area(self, obj):
        return obj.home.area if obj.home else None


class BookingCreateSerializer(serializers.ModelSerializer):
    home_status = serializers.ChoiceField(choices=Home.HomeStatus.choices, write_only=True, required=False)

    class Meta:
        model = Booking
        fields = '__all__'

    def create(self, validated_data):
        home_status = validated_data.pop('home_status', None)

        return create_booking(data=validated_data, user=self.context['request'].user, home_status=home_status)
