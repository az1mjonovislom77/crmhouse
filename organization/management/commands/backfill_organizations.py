from django.core.management.base import BaseCommand

from booking.models import Booking
from home.models import Home
from projects.models.project_models import Project
from tasks.models import Card


class Command(BaseCommand):
    help = (
        "Home, Booking, Card va Project yozuvlariga organization qiymatini mavjud "
        "bog'lanish zanjiri orqali to'ldiradi (bir marta ishga tushiriladi)"
    )

    def handle(self, *args, **options):
        project_updated = 0
        rows = Project.objects.filter(organization__isnull=True, user__organization__isnull=False).values_list(
            "pk", "user__organization_id"
        )
        for project_id, org_id in rows:
            project_updated += Project.objects.filter(pk=project_id).update(organization_id=org_id)

        home_updated = 0
        rows = Home.objects.filter(
            organization__isnull=True, blocks__projects__user__organization__isnull=False
        ).values_list("pk", "blocks__projects__user__organization_id")
        for home_id, org_id in rows:
            home_updated += Home.objects.filter(pk=home_id).update(organization_id=org_id)

        booking_updated = 0
        rows = Booking.objects.filter(
            organization__isnull=True, home__blocks__projects__user__organization__isnull=False
        ).values_list("pk", "home__blocks__projects__user__organization_id")
        for booking_id, org_id in rows:
            booking_updated += Booking.objects.filter(pk=booking_id).update(organization_id=org_id)

        card_updated = 0
        rows = Card.objects.filter(organization__isnull=True, created_by__organization__isnull=False).values_list(
            "pk", "created_by__organization_id"
        )
        for card_id, org_id in rows:
            card_updated += Card.objects.filter(pk=card_id).update(organization_id=org_id)

        self.stdout.write(
            self.style.SUCCESS(
                f"Backfill: Project {project_updated} ta, Home {home_updated} ta, "
                f"Booking {booking_updated} ta, Card {card_updated} ta organization to'ldirildi"
            )
        )
