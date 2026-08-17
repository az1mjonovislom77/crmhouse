from decimal import Decimal

from rest_framework import serializers

from booking.models import Booking
from calculator.models import CalculatorConfig, GuaranteeOption, SubsidyOption, active_guarantees, active_subsidies


class GuaranteeOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuaranteeOption
        fields = ["id", "key", "label", "percent", "is_active", "order"]


class SubsidyOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubsidyOption
        fields = ["id", "key", "label", "amount", "is_active", "order"]


class CalculatorConfigSerializer(serializers.ModelSerializer):
    guarantee_options = serializers.SerializerMethodField()
    subsidy_options = serializers.SerializerMethodField()

    class Meta:
        model = CalculatorConfig
        fields = [
            "formula_key",
            "annual_rate_pct",
            "state_threshold_pct",
            "subsidy_years",
            "firm_markup_pct",
            "round_step",
            "default_price_per_m2",
            "term_options",
            "guarantee_options",
            "subsidy_options",
        ]

    def get_guarantee_options(self, obj):
        return GuaranteeOptionSerializer(active_guarantees(obj.organization), many=True).data

    def get_subsidy_options(self, obj):
        return SubsidyOptionSerializer(active_subsidies(obj.organization), many=True).data


class CalculateInputSerializer(serializers.Serializer):
    home_id = serializers.IntegerField()
    payment_type = serializers.ChoiceField(choices=Booking.PaymentType.choices)
    guarantee_id = serializers.IntegerField(required=False)
    guarantee_key = serializers.CharField(required=False)
    subsidy_id = serializers.IntegerField(required=False)
    subsidy_key = serializers.CharField(required=False)
    credit_years = serializers.DecimalField(max_digits=4, decimal_places=2, min_value=Decimal("0.1"))
    price_per_m2 = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=False, allow_null=True, min_value=Decimal("0.01")
    )
    manual_down_payment = serializers.DecimalField(max_digits=16, decimal_places=2, required=False, allow_null=True)
    rounding = serializers.BooleanField(default=True)

    def validate(self, attrs):
        if not attrs.get("guarantee_id") and not attrs.get("guarantee_key"):
            raise serializers.ValidationError({"guarantee_id": "Kafillik turi majburiy."})
        return attrs
