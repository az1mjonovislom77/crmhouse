import re
import os
import openpyxl
from django.conf import settings
from django.core.management.base import BaseCommand

from home.models import Home
from projects.models.project_models import Block, Floors

STATUS_MAP = {
    'sotildi':                 Home.HomeStatus.SOLD,
    'band':                    Home.HomeStatus.RESERVED,
    "bo'sh":                   Home.HomeStatus.AVAILABLE,
    'bosh':                    Home.HomeStatus.AVAILABLE,
    'shartnoma':               Home.HomeStatus.RESERVED,
    'kalit topshirildi':       Home.HomeStatus.KALIT_TOPSHIRILDI,
    'nomiga otkazib berildi':  Home.HomeStatus.NOMIGA_OTKAZIB_BERILDI,
}


def parse_rooms(val):
    match = re.search(r'\d+', str(val or '1'))
    return int(match.group()) if match else 1


class Command(BaseCommand):
    help = 'home.xlsx dan Home larni import qiladi / statusni yangilaydi'

    def add_arguments(self, parser):
        parser.add_argument('--file', default='home.xlsx')
        parser.add_argument('--block-prefix', default='', help='Block title prefiks, masalan "Block "')
        parser.add_argument('--project-id', type=int, default=None)
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
        block_prefix = options['block_prefix']
        project_id = options['project_id']

        wb = openpyxl.load_workbook(file_path)
        ws = wb.active

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            bino        = row[1]   # Bino
            entrance_raw = row[2]  # Pod'ezd
            floor_raw   = row[3]   # Qavat
            home_num    = row[4]   # Xonadon raqami
            rooms_raw   = row[5]   # Xona turi
            area_raw    = row[6]   # Maydon (m²)
            price_raw   = row[7]   # 1 m² narx
            status_raw  = row[11]  # Status

            if not home_num:
                skipped_count += 1
                continue

            try:
                home_number = int(home_num)
                floor_number = int(floor_raw)
                entrance = int(entrance_raw)
                area = float(area_raw or 0)
                price_per_sqm = float(price_raw or 0)
                rooms = parse_rooms(rooms_raw)

                # Block topish
                block_title = f"{block_prefix}{bino}"
                block_qs = Block.objects.filter(title=block_title)
                if project_id:
                    block_qs = block_qs.filter(projects_id=project_id)
                block_obj = block_qs.first()

                if not block_obj:
                    self.stdout.write(self.style.WARNING(
                        f"Qator {row_idx}: Block '{block_title}' topilmadi — o'tkazildi"
                    ))
                    skipped_count += 1
                    continue

                floor_obj, _ = Floors.objects.get_or_create(number=floor_number)

                # Status aniqlash
                new_status = None
                if status_raw:
                    new_status = STATUS_MAP.get(str(status_raw).strip().lower())
                    if not new_status:
                        self.stdout.write(self.style.WARNING(
                            f"Qator {row_idx}: noma'lum status '{status_raw}'"
                        ))

                defaults = {
                    'area': area,
                    'rooms': rooms,
                    'price_per_sqm': price_per_sqm,
                    'entrance': entrance,
                }
                if new_status:
                    defaults['home_status'] = new_status

                if not dry_run:
                    _, created = Home.objects.update_or_create(
                        home_number=home_number,
                        floor=floor_obj,
                        blocks=block_obj,
                        defaults=defaults,
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                else:
                    exists = Home.objects.filter(
                        home_number=home_number, floor=floor_obj, blocks=block_obj
                    ).exists()
                    if exists:
                        updated_count += 1
                    else:
                        created_count += 1

            except Exception as e:
                self.stderr.write(f'Qator {row_idx} xato: {e}')
                error_count += 1

        label = '[DRY RUN] ' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f'\n{label}Yaratildi: {created_count} | '
            f'Yangilandi: {updated_count} | '
            f"O'tkazildi: {skipped_count} | "
            f'Xato: {error_count}'
        ))
