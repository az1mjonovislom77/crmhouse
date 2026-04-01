from rest_framework import serializers
from booking.models import Booking, PaymentTerm
from client.serializers import ClientSerializer
from home.models import Home, HomeStatusHistory


class PaymentTermSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTerm
        fields = '__all__'


class BookingGetSerializer(serializers.ModelSerializer):
    home_number = serializers.SerializerMethodField()
    payment_term_months = serializers.SerializerMethodField()
    client = ClientSerializer

    class Meta:
        model = Booking
        fields = '__all__'

    def get_home_number(self, obj):
        return obj.home.home_number if obj.home else None

    def get_payment_term_months(self, obj):
        return obj.payment_term.months if obj.payment_term else None


class BookingCreateSerializer(serializers.ModelSerializer):
    home_status = serializers.ChoiceField(choices=Home.HomeStatus.choices, write_only=True, required=False)

    class Meta:
        model = Booking
        fields = '__all__'

    def create(self, validated_data):
        home_status = validated_data.pop('home_status', None)
        booking = super().create(validated_data)

        if home_status:
            from home.services.home import HomeService

            HomeService.change_status(
                home_id=booking.home.id,
                new_status=home_status,
                user=self.context['request'].user,
                client=booking.client
            )

        return booking
