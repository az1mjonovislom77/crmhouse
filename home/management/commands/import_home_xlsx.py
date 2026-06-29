import re
import os
import openpyxl
from django.conf import settings
from django.core.management.base import BaseCommand

from home.models import Home

STATUS_MAP = {
    'sotildi':   Home.HomeStatus.SOLD,
    'band':      Home.HomeStatus.RESERVED,
    "bo'sh":     Home.HomeStatus.AVAILABLE,
    'bosh':      Home.HomeStatus.AVAILABLE,
    'shartnoma': Home.HomeStatus.RESERVED,
    'kalit topshirildi':       Home.HomeStatus.KALIT_TOPSHIRILDI,
    'nomiga otkazib berildi':  Home.HomeStatus.NOMIGA_OTKAZIB_BERILDI,
}


def parse_rooms(val):
    match = re.search(r'\d+', str(val or '1'))
    return int(match.group()) if match else 1


class Command(BaseCommand):
    help = 'home.xlsx fayldan Home statuslarini yangilaydi'

    def add_arguments(self, parser):
        parser.add_argument('--file', default='home.xlsx')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        if hasattr(self.stdout, 'reconfigure'):
            try:
                self.stdout.reconfigure(encoding='utf-8')
                self.stderr.reconfigure(encoding='utf-8')
            except Exception:
                pass

        file_path = options['file']
        if not os.path.isabs(file_path):
            file_path = os.path.join(settings.BASE_DIR, file_path)

        dry_run = options['dry_run']

        wb = openpyxl.load_workbook(file_path)
        ws = wb.active

        updated = 0
        not_found = 0
        skipped = 0
        no_status = 0

        for row in ws.iter_rows(min_row=2, values_only=True):
            home_number_raw = row[4]   # Xonadon raqami (5-ustun)
            status_raw      = row[11]  # Status (12-ustun)

            if not home_number_raw:
                skipped += 1
                continue

            try:
                home_number = int(home_number_raw)
            except (ValueError, TypeError):
                skipped += 1
                continue

            try:
                home = Home.objects.get(home_number=home_number)
            except Home.DoesNotExist:
                self.stdout.write(f'Topilmadi: home_number={home_number}')
                not_found += 1
                continue

            # Status bo'sh bo'lsa — tegmaymiz
            if not status_raw:
                no_status += 1
                continue

            new_status = STATUS_MAP.get(str(status_raw).strip().lower())
            if not new_status:
                self.stdout.write(self.style.WARNING(
                    f'home_number={home_number}: noma\'lum status "{status_raw}"'
                ))
                skipped += 1
                continue

            if not dry_run:
                home.home_status = new_status
                home.save(update_fields=['home_status'])

            self.stdout.write(
                f'{"[DRY] " if dry_run else ""}'
                f'home_number={home_number}: {home.home_status} → {new_status}'
            )
            updated += 1

        label = '[DRY RUN] ' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f'\n{label}Yangilandi: {updated} | '
            f'Topilmadi: {not_found} | '
            f'Status yo\'q: {no_status} | '
            f'O\'tkazildi: {skipped}'
        ))
