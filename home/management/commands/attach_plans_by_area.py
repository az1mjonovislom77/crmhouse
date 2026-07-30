import os
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from home.models import FloorPlan, Home

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif")


class Command(BaseCommand):
    help = (
        "Berilgan papkadagi barcha rasmlarni tanlangan organization ichidagi, "
        "area si berilgan qiymatga teng bo'lgan BARCHA homelarga floor plan qilib qo'shadi.\n"
        'Misol: python manage.py attach_plans_by_area --org "Paxtazor Xonadonlar" --area 76 --images-dir images'
    )

    def add_arguments(self, parser):
        parser.add_argument("--org", default="Paxtazor Xonadonlar", help="Organization nomi")
        parser.add_argument("--area", default="76", help="Home area qiymati (masalan: 76)")
        parser.add_argument("--images-dir", default="images", help="Rasmlar papkasi (BASE_DIR ga nisbatan)")
        parser.add_argument(
            "--files",
            nargs="*",
            help="Faqat shu fayllarni yuklash (papka ichidagi nomlari). Berilmasa — papkadagi barcha rasmlar",
        )
        parser.add_argument(
            "--clear", action="store_true", help="Avval shu homelardagi mavjud floor planlarni o'chirish"
        )
        parser.add_argument("--dry-run", action="store_true", help="Bazaga yozmasdan faqat rejani ko'rsatish")

    def handle(self, *args, **options):
        org_name = options["org"]

        try:
            area = Decimal(str(options["area"]))
        except (InvalidOperation, TypeError, ValueError):
            self.stdout.write(self.style.ERROR(f"--area noto'g'ri: \"{options['area']}\""))
            return

        images_dir = os.path.join(settings.BASE_DIR, options["images_dir"])
        if not os.path.isdir(images_dir):
            self.stdout.write(self.style.ERROR(f"Papka topilmadi: {images_dir}"))
            return

        if options["files"]:
            files = []
            for fname in options["files"]:
                if not os.path.isfile(os.path.join(images_dir, fname)):
                    self.stdout.write(self.style.ERROR(f"Fayl topilmadi: {os.path.join(images_dir, fname)}"))
                    return
                files.append(fname)
        else:
            files = [f for f in sorted(os.listdir(images_dir)) if f.lower().endswith(IMAGE_EXTS)]

        if not files:
            self.stdout.write(self.style.ERROR(f"{images_dir} ichida rasm topilmadi"))
            return

        homes = list(Home.objects.filter(organization__name=org_name, area=area).order_by("home_number"))
        if not homes:
            self.stdout.write(self.style.ERROR(f'"{org_name}" ichida area={area} bo\'lgan home topilmadi'))
            return

        self.stdout.write(f"Reja (org: {org_name}, area: {area}):")
        self.stdout.write(f"  {len(homes)} ta home: {[h.home_number for h in homes]}")
        self.stdout.write(f"  {len(files)} ta rasm: {files}")
        self.stdout.write(self.style.SUCCESS(f"Jami {len(homes) * len(files)} ta floor plan qo'shiladi."))

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry-run: bazaga hech narsa yozilmadi."))
            return

        if options["clear"]:
            deleted, _ = FloorPlan.objects.filter(home__in=homes).delete()
            self.stdout.write(self.style.WARNING(f"{deleted} ta mavjud floor plan o'chirildi"))

        # Har bir rasm faylini diskka bir marta yuklaymiz, qolgan homelar shu faylga ulanadi
        masters = {}
        for fname in files:
            plan = FloorPlan(home=homes[0])
            with open(os.path.join(images_dir, fname), "rb") as f:
                plan.image.save(fname, File(f), save=True)
            masters[fname] = plan
            self.stdout.write(f"Yuklandi: {fname} -> {plan.image.name}")

        to_create = [FloorPlan(home=home, image=masters[fname].image.name) for home in homes[1:] for fname in files]
        FloorPlan.objects.bulk_create(to_create)

        self.stdout.write(
            self.style.SUCCESS(
                f"Natija: {len(to_create) + len(masters)} ta floor plan qo'shildi ({len(homes)} ta homega)."
            )
        )
