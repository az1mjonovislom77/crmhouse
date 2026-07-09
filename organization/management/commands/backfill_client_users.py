from django.core.management.base import BaseCommand

from booking.models import Booking
from client.models import Client


class Command(BaseCommand):
    help = "Client yozuvlariga user (egasi) va organization qiymatini to'ldiradi"

    def handle(self, *args, **options):
        updated = 0
        rows = Booking.objects.filter(client__user__isnull=True).values_list(
            'client_id', 'home__blocks__projects__user_id'
        )
        for client_id, user_id in rows:
            if user_id:
                updated += Client.objects.filter(
                    pk=client_id, user__isnull=True
                ).update(user_id=user_id)

        orgs = Client.objects.filter(
            organization__isnull=True, user__organization__isnull=False
        ).values_list('pk', 'user__organization_id')
        org_updated = 0
        for client_id, org_id in orgs:
            org_updated += Client.objects.filter(pk=client_id).update(organization_id=org_id)

        self.stdout.write(self.style.SUCCESS(
            f"Client: {updated} ta user, {org_updated} ta organization yangilandi"))
