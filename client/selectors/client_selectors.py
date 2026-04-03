from django.db.models import Prefetch
from booking.models import Booking
from home.models import HomeStatusHistory
from client.models import Client


def get_client_queryset():
    return Client.objects.prefetch_related(
        Prefetch("bookings", queryset=Booking.objects.select_related("home").prefetch_related(
            Prefetch("home__status_history",
                     queryset=HomeStatusHistory.objects.select_related(
                         "home", "home__blocks", "home__floor", "changed_by", ), to_attr="prefetched_history"))))
