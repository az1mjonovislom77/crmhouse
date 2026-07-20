from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from booking.models import Booking, Company, Payment
from client.api.serializers import ClientNestSerializer
from common.base.serializers_base import BaseReadSerializer
from home.models import Home


class CompanySerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Company


class BookingGetSerializer(serializers.ModelSerializer):
    home_number = serializers.SerializerMethodField()
    client = ClientNestSerializer(read_only=True)
    block_title = serializers.SerializerMethodField()
    floor_number = serializers.SerializerMethodField()
    total_area = serializers.SerializerMethodField()
    rooms_number = serializers.SerializerMethodField()
    entrance = serializers.SerializerMethodField()
    price_per_sqm = serializers.SerializerMethodField()
    company = CompanySerializer(read_only=True)
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total_price_inword = serializers.CharField(read_only=True)
    manual_down_payment_inword = serializers.CharField(read_only=True)
    client_payment_inword = serializers.CharField(read_only=True)
    remaining_debt = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'

    def get_home_number(self, obj):
        return obj.home.home_number if obj.home else None

    def get_block_title(self, obj):
        return obj.home.blocks.title if obj.home and obj.home.blocks else None

    def get_floor_number(self, obj):
        return obj.home.floor.number if obj.home and obj.home.floor else None

    def get_rooms_number(self, obj):
        return obj.home.rooms if obj.home and obj.home.rooms else None

    def get_total_area(self, obj):
        return obj.home.area if obj.home else None

    def get_entrance(self, obj):
        return obj.home.entrance if obj.home else None

    def get_price_per_sqm(self, obj):
        return obj.home.price_per_sqm if obj.home else None


def _home_org_id(home):
    block = home.blocks
    project = block.projects if block else None
    return project.organization_id if project else None


def _require_same_org(serializer, attrs, home=None, client=None, booking=None):
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
    guarantee_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    subsidy_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = Booking
        fields = '__all__'

        read_only_fields = [
            'created_at', 'organization', 'status',
            'price_per_m2', 'guarantee_percent', 'subsidy_amount',
            'annual_rate_pct', 'state_threshold_pct', 'subsidy_years', 'firm_markup_pct',
            'contract_price', 'firm_covers', 'client_payment', 'credit_amount',
            'monthly_full', 'monthly_stage1', 'gov_monthly',
        ]

    def validate(self, attrs):
        home = attrs.get('home') or (self.instance.home if self.instance else None)
        client = attrs.get('client') or (self.instance.client if self.instance else None)
        _require_same_org(self, attrs, home=home, client=client)

        guarantee_id = attrs.pop('guarantee_id', None)
        subsidy_id = attrs.pop('subsidy_id', None)

        def current(field):
            if field in attrs:
                return attrs[field]
            return getattr(self.instance, field, None)

        payment_type = current('payment_type')
        credit_years = current('credit_years')

        if payment_type and guarantee_id and credit_years and home is not None:
            from calculator.services import compute_booking_snapshot
            request = self.context.get('request')
            organization = getattr(request.user, 'organization', None) if request else None
            snapshot = compute_booking_snapshot(
                home=home,
                payment_type=payment_type,
                guarantee_id=guarantee_id,
                subsidy_id=subsidy_id,
                credit_years=credit_years,
                manual_down_payment=current('manual_down_payment'),
                organization=organization,
            )
            attrs.update(snapshot)
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
        if hasattr(obj, 'booking_payments_total') and obj.booking_payments_total is not None:
            paid = obj.booking_payments_total
        else:
            paid = booking.payments.aggregate(total=Sum('amount'))['total'] or 0
        return total_price - paid
