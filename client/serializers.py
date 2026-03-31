from rest_framework import serializers
from booking.models import Booking
from client.models import Client
from home.api.serializers.home_serializers import HomeStatusHistorySerializer


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
    booking = BookingNestSerializer(source='bookings', many=True, read_only=True)
    home_status_history = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = ['id', 'booking', 'home_status_history', 'full_name', 'phone_number', 'passport', 'address']

    def get_home_status_history(self, obj):
        history = []

        for booking in obj.bookings.all():
            home = booking.home

            if hasattr(home, "prefetched_history"):
                history.extend(home.prefetched_history)

        unique = {h.id: h for h in history}.values()

        return HomeStatusHistorySerializer(unique, many=True).data
