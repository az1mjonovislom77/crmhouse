from decimal import Decimal
from django.db.models import Prefetch, Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from booking.models import Booking
from home.models import HomeStatusHistory
from client.models import Client


def get_client_queryset():
    bookings_qs = Booking.objects.select_related(
        "home", "home__renovation"
    ).annotate(
        payments_total=Coalesce(Sum('payments__amount'), Value(Decimal('0')), output_field=DecimalField())
    )
    return Client.objects.select_related("user", "organization").prefetch_related(
        Prefetch("bookings", queryset=bookings_qs),
        Prefetch("status_history",
                 queryset=HomeStatusHistory.objects.select_related("home", "home__blocks", "home__floor", "changed_by")))
