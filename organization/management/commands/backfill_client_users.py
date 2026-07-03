"""Mavjud mijozlarga user (egasi) qiymatini to'ldiruvchi bir martalik buyruq.

Client.user yangi qo'shilgan maydon — eski mijozlar uchun booking zanjiri
orqali tiklanadi: client -> booking -> home -> block -> project -> user.
Tashkilot userdan aniqlanadi, shuning uchun alohida organization saqlanmaydi.

Ishga tushirish: python manage.py backfill_client_users
"""
from django.core.management.base import BaseCommand

from booking.models import Booking
from client.models import Client


class Command(BaseCommand):
    help = "Client yozuvlariga user (egasi) qiymatini to'ldiradi"

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

        self.stdout.write(self.style.SUCCESS(f"Client: {updated} ta yangilandi"))
