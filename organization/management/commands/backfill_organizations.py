from django.core.management.base import BaseCommand

from booking.models import Booking
from home.models import Home
from tasks.models import Card


class Command(BaseCommand):
    help = ("Home, Booking va Card yozuvlariga organization qiymatini mavjud "
            "bog'lanish zanjiri orqali to'ldiradi (bir marta ishga tushiriladi)")

    def handle(self, *args, **options):
        home_updated = 0
        rows = Home.objects.filter(
            organization__isnull=True, blocks__projects__user__organization__isnull=False
        ).values_list('pk', 'blocks__projects__user__organization_id')
        for home_id, org_id in rows:
            home_updated += Home.objects.filter(pk=home_id).update(organization_id=org_id)

        booking_updated = 0
        rows = Booking.objects.filter(
            organization__isnull=True, home__blocks__projects__user__organization__isnull=False
        ).values_list('pk', 'home__blocks__projects__user__organization_id')
        for booking_id, org_id in rows:
            booking_updated += Booking.objects.filter(pk=booking_id).update(organization_id=org_id)

        card_updated = 0
        rows = Card.objects.filter(
            organization__isnull=True, created_by__organization__isnull=False
        ).values_list('pk', 'created_by__organization_id')
        for card_id, org_id in rows:
            card_updated += Card.objects.filter(pk=card_id).update(organization_id=org_id)

        self.stdout.write(self.style.SUCCESS(
            f"Backfill: Home {home_updated} ta, Booking {booking_updated} ta, "
            f"Card {card_updated} ta organization to'ldirildi"))
