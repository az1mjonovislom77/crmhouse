from datetime import date
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce, TruncMonth

from booking.models import Booking, Payment
from common.utils import MONTH_LABELS_UZ, apply_date_range, last_months, local_day_start, to_millions

MONEY: DecimalField = DecimalField(max_digits=16, decimal_places=2)
ZERO = Value(Decimal("0"), output_field=MONEY)

CONTRACT_PRICE = Coalesce(F("home__area") * F("home__price_per_sqm"), ZERO) + Coalesce(
    F("home__renovation__price"), ZERO
)


def get_total_contract(date_from=None, date_to=None):
    qs = Booking.objects.exclude(status=Booking.BookingStatus.CANCELED)
    return apply_date_range(qs, "created_at", date_from, date_to)


def get_total_contract_price(qs):
    result = qs.aggregate(total=Coalesce(Sum(CONTRACT_PRICE, output_field=MONEY), ZERO))
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
    total_price = CONTRACT_PRICE

    paid_subquery = (
        Payment.objects.filter(booking=OuterRef("pk")).values("booking").annotate(total=Sum("amount")).values("total")
    )

    remaining = ExpressionWrapper(
        total_price - Coalesce(Subquery(paid_subquery, output_field=MONEY), ZERO),
        output_field=MONEY,
    )

    result = qs.annotate(remaining=remaining).aggregate(total=Coalesce(Sum("remaining"), ZERO))
    return result["total"]


def get_monthly_revenue(booking_qs, payment_qs, months=8):
    window = last_months(months)
    start = date(window[0][0], window[0][1], 1)

    contract_rows = (
        booking_qs.filter(created_at__gte=local_day_start(start))
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Sum(CONTRACT_PRICE, output_field=MONEY))
    )
    collected_rows = (
        payment_qs.filter(payment_date__gte=start)
        .annotate(month=TruncMonth("payment_date"))
        .values("month")
        .annotate(total=Sum("amount"))
    )
    contract = {(r["month"].year, r["month"].month): r["total"] for r in contract_rows}
    collected = {(r["month"].year, r["month"].month): r["total"] for r in collected_rows}

    return [
        {
            "month": MONTH_LABELS_UZ[month - 1],
            "contract": to_millions(contract.get((year, month))),
            "collected": to_millions(collected.get((year, month))),
        }
        for year, month in window
    ]
