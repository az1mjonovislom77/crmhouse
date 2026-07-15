from collections import defaultdict
from io import BytesIO
from typing import Any

import pillow_heif
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from PIL import Image

from home.models import FloorPlan
from projects.models.project_models import BlockImage, Project
from projects.models.showroom_models import ShowroomImage

pillow_heif.register_heif_opener()

TARGETS: list[tuple[Any, str]] = [
    (FloorPlan, 'image'),
    (Project, 'image'),
    (BlockImage, 'image'),
    (ShowroomImage, 'image'),
]


def reencode(raw_bytes, quality, max_width):
    img: Image.Image = Image.open(BytesIO(raw_bytes))
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGBA' if 'A' in img.getbands() or img.mode == 'P' else 'RGB')
    if img.width > max_width:
        ratio = max_width / float(img.width)
        img = img.resize((max_width, int(img.height * ratio)), Image.Resampling.LANCZOS)
    out = BytesIO()
    img.save(out, format='WEBP', quality=quality)
    return out.getvalue()


class Command(BaseCommand):
    help = ("Bazadagi rasmlarni webp'ga qayta siqadi. Bir nechta yozuv bitta faylni "
            "ulashsa ham to'g'ri ishlaydi. --repair: buzilgan yo'llarni mavjud .webp'ga qaytaradi.")

    def add_arguments(self, parser):
        parser.add_argument('--quality', type=int, default=80, help="webp sifati (0-100), default 80")
        parser.add_argument('--max-width', type=int, default=1200, help="maksimal eni (px), default 1200")
        parser.add_argument('--dry-run', action='store_true', help="hech narsa yozmaydi, faqat hisobot")
        parser.add_argument('--repair', action='store_true',
                            help="qayta siqmaydi; fayli yo'q yozuvlarni mavjud .webp variantiga qaytaradi")

    def handle(self, *args, **opts):
        if opts['repair']:
            return self._repair(dry=opts['dry_run'])
        return self._reoptimize(opts['quality'], opts['max_width'], opts['dry_run'])

    def _repair(self, dry):
        repaired = still_missing = 0
        for model, field_name in TARGETS:
            qs = (model.objects
                  .exclude(**{field_name: ''})
                  .exclude(**{f'{field_name}__isnull': True}))
            for obj in qs.iterator():
                name = getattr(obj, field_name).name
                if not name or default_storage.exists(name):
                    continue
                webp = name.rsplit('.', 1)[0] + '.webp'
                if default_storage.exists(webp):
                    if not dry:
                        model.objects.filter(pk=obj.pk).update(**{field_name: webp})
                    repaired += 1
                else:
                    still_missing += 1
                    self.stderr.write(f"  hali yo'q: {model.__name__}#{obj.pk} {name}")
        prefix = "[DRY-RUN] " if dry else ""
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}Tuzatildi: {repaired} | hali yo'q (.webp topilmadi): {still_missing}"))

    def _reoptimize(self, quality, max_width, dry):
        total_before = total_after = 0
        files_done = records = missing = errors = 0

        for model, field_name in TARGETS:
            qs = (model.objects
                  .exclude(**{field_name: ''})
                  .exclude(**{f'{field_name}__isnull': True}))
            groups = defaultdict(list)
            for obj in qs.iterator():
                name = getattr(obj, field_name).name
                if name:
                    groups[name].append(obj.pk)

            for old_name, pks in groups.items():
                if not default_storage.exists(old_name):
                    missing += len(pks)
                    continue
                try:
                    with default_storage.open(old_name, 'rb') as f:
                        raw = f.read()
                    webp = reencode(raw, quality, max_width)
                    new_name = old_name.rsplit('.', 1)[0] + '.webp'
                    total_before += len(raw)
                    total_after += len(webp)
                    files_done += 1
                    records += len(pks)
                    if dry:
                        continue
                    if default_storage.exists(new_name):
                        default_storage.delete(new_name)
                    default_storage.save(new_name, ContentFile(webp))
                    model.objects.filter(pk__in=pks).update(**{field_name: new_name})
                    if new_name != old_name and default_storage.exists(old_name):
                        default_storage.delete(old_name)
                except Exception as e:
                    errors += 1
                    self.stderr.write(f"  XATO: {model.__name__} {old_name}: {e}")

        def mb(b):
            return round(b / 1024 / 1024, 2)

        prefix = "[DRY-RUN] " if dry else ""
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}Fayllar: {files_done} | yozuvlar: {records} | fayli yo'q: {missing} | xato: {errors} | "
            f"hajm: {mb(total_before)}MB -> {mb(total_after)}MB (tejaldi: {mb(total_before - total_after)}MB)"))
