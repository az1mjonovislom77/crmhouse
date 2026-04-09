from decimal import Decimal
from rest_framework import serializers
from booking.models import Booking
from client.models import Client
from home.api.home_serializers import HomeStatusHistorySerializer


class BookingNestSerializer(serializers.ModelSerializer):
    home_number = serializers.SerializerMethodField()
    payment_term_months = serializers.SerializerMethodField()
    home_status = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = '__all__'

    def get_home_number(self, obj):
        return obj.home.home_number if obj.home else None

    def get_payment_term_months(self, obj):
        return obj.payment_term.months if obj.payment_term else None

    def get_home_status(self, obj):
        return obj.home.home_status if obj.home else None


class BookingMiniSerializer(serializers.ModelSerializer):
    cash_payment_percent = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = '__all__'

    def get_cash_payment_percent(self, obj):
        if not obj.home:
            return None
        total_price = (((obj.home.area or 0) * (obj.home.price_per_sqm or 0)) +
                       (obj.home.renovation.price if obj.home.renovation else 0))

        if not total_price:
            return 0

        percent = (obj.cash_payment / Decimal(total_price)) * Decimal(100)
        return round(percent, 2)


class ClientSerializer(serializers.ModelSerializer):
    booking = BookingNestSerializer(source='bookings', many=True, read_only=True)
    home_status_history = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = ['id', 'booking', 'home_status_history', 'full_name', 'phone_number', 'passport', 'address']

    def get_home_status_history(self, obj):
        return HomeStatusHistorySerializer(obj.status_history.all(), many=True).data


class ClientNestSerializer(serializers.ModelSerializer):
    home_status_history = serializers.SerializerMethodField()
    booking = BookingMiniSerializer(source='bookings', read_only=True)

    class Meta:
        model = Client
        fields = ['id', 'booking', 'home_status_history', 'full_name', 'phone_number', 'passport', 'address']

    def get_home_status_history(self, obj):
        return HomeStatusHistorySerializer(obj.status_history.all(), many=True).data
