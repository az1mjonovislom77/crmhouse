from decimal import Decimal
from django.db.models import F, Sum, Value, DecimalField, ExpressionWrapper, OuterRef, Subquery
from django.db.models.functions import Coalesce
from booking.models import Booking, Payment
from common.utils import apply_date_range

MONEY = DecimalField(max_digits=16, decimal_places=2)
ZERO = Value(Decimal("0"), output_field=MONEY)


def get_total_contract(date_from=None, date_to=None):
    return apply_date_range(Booking.objects.all(), 'created_at', date_from, date_to)


def get_total_contract_price(qs):
    price = (Coalesce(F("home__area") * F("home__price_per_sqm"), ZERO)
             + Coalesce(F("home__renovation__price"), ZERO))
    result = qs.aggregate(total=Coalesce(Sum(price, output_field=MONEY), ZERO))
    return result["total"]


def get_total_payments(date_from=None, date_to=None):
    qs = Payment.objects.all()
    if date_from:
        qs = qs.filter(payment_date__gte=date_from)
    if date_to:
        qs = qs.filter(payment_date__lte=date_to)
    return qs


def get_total_payments_price(qs):
    result = qs.aggregate(total=Coalesce(Sum("amount"), ZERO))
    return result["total"]


def get_total_unpaid(qs):
    total_price = (Coalesce(F("home__area") * F("home__price_per_sqm"), ZERO)
                   + Coalesce(F("home__renovation__price"), ZERO))

    paid_subquery = (
        Payment.objects.filter(booking=OuterRef("pk"))
        .values("booking")
        .annotate(total=Sum("amount"))
        .values("total")
    )

    remaining = ExpressionWrapper(
        total_price
        - (total_price * Coalesce(F("down_payment"), Value(0)) / Value(100))
        - F("cash_payment")
        - Coalesce(Subquery(paid_subquery, output_field=MONEY), ZERO),
        output_field=MONEY,
    )

    result = qs.annotate(remaining=remaining).aggregate(total=Coalesce(Sum("remaining"), ZERO))
    return result["total"]
