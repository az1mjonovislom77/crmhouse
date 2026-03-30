from rest_framework import serializers

from booking.models import Booking
from client.models import Client
from home.serializers import HomeStatusHistorySerializer


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


class ClientSerializer(serializers.ModelSerializer):
    booking = BookingNestSerializer(many=True, read_only=True)
    home_status_history = HomeStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Client
        fields = '__all__'
