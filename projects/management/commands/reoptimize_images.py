from io import BytesIO

import pillow_heif
from PIL import Image
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from home.models import FloorPlan
from projects.models.project_models import Project, Block
from projects.models.showroom_models import ShowroomImage

pillow_heif.register_heif_opener()

# (model, image field name) — bazadagi barcha haqiqiy rasm maydonlari
TARGETS = [
    (FloorPlan, 'image'),
    (Project, 'image'),
    (Block, 'image'),
    (ShowroomImage, 'image'),
]


def reencode(raw_bytes, quality, max_width):
    img = Image.open(BytesIO(raw_bytes))
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGBA' if 'A' in img.getbands() or img.mode == 'P' else 'RGB')
    if img.width > max_width:
        ratio = max_width / float(img.width)
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
    out = BytesIO()
    img.save(out, format='WEBP', quality=quality)
    return out.getvalue()


class Command(BaseCommand):
    help = "Bazadagi barcha rasmlarni webp'ga qayta siqadi (fayl o'rniga yoziladi). Orqaga qaytmaydi!"

    def add_arguments(self, parser):
        parser.add_argument('--quality', type=int, default=80, help="webp sifati (0-100), default 80")
        parser.add_argument('--max-width', type=int, default=1200, help="maksimal eni (px), default 1200")
        parser.add_argument('--dry-run', action='store_true', help="hech narsa yozmaydi, faqat hisobot")

    def handle(self, *args, **opts):
        quality = opts['quality']
        max_width = opts['max_width']
        dry = opts['dry_run']

        total_before = total_after = 0
        processed = missing = errors = 0

        for model, field_name in TARGETS:
            qs = (model.objects
                  .exclude(**{field_name: ''})
                  .exclude(**{f'{field_name}__isnull': True}))
            seen = 0
            for obj in qs.iterator():
                field = getattr(obj, field_name)
                if not field:
                    continue
                seen += 1
                old_name = field.name
                if not default_storage.exists(old_name):
                    missing += 1
                    self.stderr.write(f"  yo'q: {model.__name__}#{obj.pk} {old_name}")
                    continue
                try:
                    with default_storage.open(old_name, 'rb') as f:
                        raw = f.read()
                    webp = reencode(raw, quality, max_width)
                    new_name = old_name.rsplit('.', 1)[0] + '.webp'
                    total_before += len(raw)
                    total_after += len(webp)
                    processed += 1
                    if dry:
                        continue
                    if default_storage.exists(new_name):
                        default_storage.delete(new_name)
                    default_storage.save(new_name, ContentFile(webp))
                    model.objects.filter(pk=obj.pk).update(**{field_name: new_name})
                    if new_name != old_name and default_storage.exists(old_name):
                        default_storage.delete(old_name)
                except Exception as e:
                    errors += 1
                    self.stderr.write(f"  XATO: {model.__name__}#{obj.pk} {old_name}: {e}")
            self.stdout.write(f"{model.__name__}: {seen} ta rasm ko'rildi")

        def mb(b):
            return round(b / 1024 / 1024, 2)

        prefix = "[DRY-RUN] " if dry else ""
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}Qayta siqildi: {processed} | topilmadi: {missing} | xato: {errors} | "
            f"hajm: {mb(total_before)}MB -> {mb(total_after)}MB "
            f"(tejaldi: {mb(total_before - total_after)}MB)"))
