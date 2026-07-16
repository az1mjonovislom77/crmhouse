from rest_framework import serializers

from booking.models import Booking
from client.models import Client
from home.api.home_serializers import HomeStatusHistorySerializer


class BookingNestSerializer(serializers.ModelSerializer):
    home_number = serializers.SerializerMethodField()
    home_status = serializers.SerializerMethodField()
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    remaining_debt = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'

    def get_home_number(self, obj):
        return obj.home.home_number if obj.home else None

    def get_home_status(self, obj):
        return obj.home.home_status if obj.home else None


class BookingMiniSerializer(serializers.ModelSerializer):
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    remaining_debt = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'


class ClientSerializer(serializers.ModelSerializer):
    booking = BookingNestSerializer(source='bookings', many=True, read_only=True)
    home_status_history = serializers.SerializerMethodField()
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True, default=None)
    organization = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Client
        fields = ['id', 'booking', 'home_status_history', 'full_name', 'phone_number', 'phone_number2', 'passport',
                  'passport_date', 'address', 'from_who', 'user', 'user_full_name', 'organization']

    def get_home_status_history(self, obj):
        return HomeStatusHistorySerializer(obj.status_history.all(), many=True).data


class ClientNestSerializer(serializers.ModelSerializer):
    home_status_history = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = ['id', 'home_status_history', 'full_name', 'phone_number', 'phone_number2', 'passport',
                  'passport_date', 'address', 'from_who']

    def get_home_status_history(self, obj):
        return HomeStatusHistorySerializer(obj.status_history.all(), many=True).data
