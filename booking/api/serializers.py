from decimal import Decimal
from django.db.models import Sum
from rest_framework import serializers
from booking.models import Booking, PaymentTerm, Company, Payment
from client.api.serializers import ClientNestSerializer
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
    client = ClientNestSerializer(read_only=True)
    block_title = serializers.SerializerMethodField()
    floor_number = serializers.SerializerMethodField()
    total_area = serializers.SerializerMethodField()
    rooms_number = serializers.SerializerMethodField()
    company = CompanySerializer(read_only=True)
    cash_payment_percent = serializers.SerializerMethodField()
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    remaining_debt = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'

    def get_home_number(self, obj):
        return obj.home.home_number if obj.home else None

    def get_payment_term_months(self, obj):
        return obj.payment_term.months if obj.payment_term else None

    def get_block_title(self, obj):
        return obj.home.blocks.title if obj.home and obj.home.blocks else None

    def get_floor_number(self, obj):
        return obj.home.floor.number if obj.home and obj.home.floor else None

    def get_rooms_number(self, obj):
        return obj.home.rooms if obj.home and obj.home.rooms else None

    def get_total_area(self, obj):
        return obj.home.area if obj.home else None

    def get_cash_payment_percent(self, obj):
        if not obj.home:
            return None
        total_price = (((obj.home.area or 0) * (obj.home.price_per_sqm or 0)) +
                       (obj.home.renovation.price if obj.home.renovation else 0))

        if not total_price:
            return 0

        percent = (obj.cash_payment / Decimal(total_price)) * Decimal(100)
        return round(percent, 2)


def _home_org_id(home):
    """Organization id of the home via block -> project -> owner chain, or None."""
    block = home.blocks
    project = block.projects if block else None
    owner = project.user if project else None
    return owner.organization_id if owner else None


def _require_same_org(serializer, attrs, home=None, client=None, booking=None):
    """Rejects writes that target another organization's objects (staff bypasses)."""
    request = serializer.context.get('request')
    if request is None or request.user.is_staff:
        return
    org_id = request.user.organization_id
    if org_id is None:
        raise serializers.ValidationError("Sizga tashkilot biriktirilmagan.")
    if home is not None and _home_org_id(home) != org_id:
        raise serializers.ValidationError({"home": "Bu uy sizning tashkilotingizga tegishli emas."})
    if client is not None:
        client_org_id = client.user.organization_id if client.user else None
        if client_org_id != org_id:
            raise serializers.ValidationError({"client": "Bu mijoz sizning tashkilotingizga tegishli emas."})
    if booking is not None and _home_org_id(booking.home) != org_id:
        raise serializers.ValidationError({"booking": "Bu booking sizning tashkilotingizga tegishli emas."})


class BookingCreateSerializer(serializers.ModelSerializer):
    home_status = serializers.ChoiceField(choices=Home.HomeStatus.choices, required=False)

    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['created_at']

    def validate_cash_payment(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Summa manfiy bo'lishi mumkin emas.")
        return value

    def validate(self, attrs):
        home = attrs.get('home') or (self.instance.home if self.instance else None)
        client = attrs.get('client') or (self.instance.client if self.instance else None)
        _require_same_org(self, attrs, home=home, client=client)
        return attrs


class PaymentSerializer(serializers.ModelSerializer):
    remaining_debt = serializers.SerializerMethodField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0.01'))

    class Meta:
        model = Payment
        fields = ['id', 'booking', 'amount', 'note', 'created_at', 'remaining_debt', 'payment_date', 'payment_data',
                  'payment_number', 'file']
        read_only_fields = ['id', 'created_at', 'remaining_debt']

    def validate(self, attrs):
        booking = attrs.get('booking') or (self.instance.booking if self.instance else None)
        if self.instance is not None and 'booking' in attrs and attrs['booking'].pk != self.instance.booking_id:
            raise serializers.ValidationError({"booking": "To'lovning bookingini o'zgartirib bo'lmaydi."})
        _require_same_org(self, attrs, booking=booking)
        return attrs

    def get_remaining_debt(self, obj):
        booking = obj.booking
        total_price = booking.total_price
        down_payment_amount = (total_price * booking.down_payment / 100) if booking.down_payment is not None else 0
        if hasattr(obj, 'booking_payments_total') and obj.booking_payments_total is not None:
            paid = obj.booking_payments_total
        else:
            paid = booking.payments.aggregate(total=Sum('amount'))['total'] or 0
        return total_price - booking.cash_payment - down_payment_amount - paid
