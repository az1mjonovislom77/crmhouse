import os

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from home.models import FloorPlan, Home
from projects.models.project_models import Block


class Command(BaseCommand):
    help = (
        "Home number bo'yicha cycling tartibida floor plan qo'shadi: "
        "1-home -> 1-rasm, 2-home -> 2-rasm, ... , keyin yana boshidan.\n"
        "Misol: python manage.py add_plans_by_home_number "
        '--org "Qamashi Xonadonlar" --block "Block - A" '
        "--images-dir data/home --order Aa2.png,Aa3.png,Aa4.png,Aa1.png\n"
        "Oraliq va boshlanish nuqtasi bilan: python manage.py add_plans_by_home_number "
        '--org "Paxtazor Xonadonlar" --block "Block - B" --from-number 33 --to-number 72 '
        "--images-dir . --order 1.jpg,2.jpg,3.jpg,4.jpg,5.jpg"
    )

    def add_arguments(self, parser):
        parser.add_argument("--org", default="Qamashi Xonadonlar", help="Organization nomi")
        parser.add_argument("--block", default="Block - A", help="Block title")
        parser.add_argument("--images-dir", default="data/home", help="Rasmlar papkasi (BASE_DIR ga nisbatan)")
        parser.add_argument(
            "--order",
            default="Aa2.png,Aa3.png,Aa4.png,Aa1.png",
            help="Rasmlar tartibi (vergul bilan): 1-home shu ro'yxatdagi 1-rasmni oladi va hokazo",
        )
        parser.add_argument("--from-number", type=int, help="Faqat shu home_number dan boshlab (masalan: 33)")
        parser.add_argument("--to-number", type=int, help="Faqat shu home_number gacha, o'zi ham kiradi (masalan: 72)")
        parser.add_argument(
            "--start",
            type=int,
            help="Cycling shu home_number dan boshlanadi (u 1-rasmni oladi). "
            "Berilmasa: --from-number, u ham bo'lmasa 1",
        )
        parser.add_argument(
            "--clear", action="store_true", help="Avval shu homelardagi mavjud floor planlarni o'chirish"
        )
        parser.add_argument("--dry-run", action="store_true", help="Bazaga yozmasdan faqat rejani ko'rsatish")

    def handle(self, *args, **options):
        org_name = options["org"]
        block_title = options["block"]
        dry_run = options["dry_run"]

        # Block title org bo'yicha unique emas — shu org homelariga tegishlilarini olamiz
        blocks = list(Block.objects.filter(title=block_title, homes__organization__name=org_name).distinct())
        if not blocks:
            self.stdout.write(self.style.ERROR(f'"{org_name}" ichida block topilmadi: "{block_title}"'))
            self.stdout.write(
                "Mavjud blocklar: "
                + ", ".join(
                    sorted(
                        Block.objects.filter(homes__organization__name=org_name)
                        .values_list("title", flat=True)
                        .distinct()
                    )
                )
            )
            return
        if len(blocks) > 1:
            self.stdout.write(
                self.style.WARNING(f'"{block_title}" nomli {len(blocks)} ta block topildi — hammasi olinadi')
            )

        images_dir = os.path.join(settings.BASE_DIR, options["images_dir"])
        image_files = [name.strip() for name in options["order"].split(",") if name.strip()]

        missing = [name for name in image_files if not os.path.exists(os.path.join(images_dir, name))]
        if missing:
            self.stdout.write(self.style.ERROR(f"Rasm topilmadi ({images_dir}): {missing}"))
            return

        homes_qs = Home.objects.filter(blocks__in=blocks, organization__name=org_name)
        if options["from_number"] is not None:
            homes_qs = homes_qs.filter(home_number__gte=options["from_number"])
        if options["to_number"] is not None:
            homes_qs = homes_qs.filter(home_number__lte=options["to_number"])
        homes = list(homes_qs.order_by("home_number").distinct())
        if not homes:
            self.stdout.write(self.style.ERROR(f'"{org_name}" + "{block_title}" bo\'yicha home topilmadi'))
            return

        # Cycling sanog'i qayerdan boshlanishi: --start, bo'lmasa --from-number, u ham bo'lmasa 1
        start = options["start"] or options["from_number"] or 1

        cycle = len(image_files)
        self.stdout.write(f"{len(homes)} ta home topildi. Rasmlar tartibi: {image_files}")
        self.stdout.write(f"Cycling boshlanishi: home_number={start} -> {image_files[0]}")

        for home in homes:
            idx = (home.home_number - start) % cycle
            self.stdout.write(f"  home_number={home.home_number} (id={home.pk}) -> {image_files[idx]}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run: bazaga hech narsa yozilmadi."))
            return

        if options["clear"]:
            deleted, _ = FloorPlan.objects.filter(home__in=homes).delete()
            self.stdout.write(self.style.WARNING(f"{deleted} ta mavjud floor plan o'chirildi"))

        master_plans = {}
        for img_name in image_files:
            plan = FloorPlan()
            with open(os.path.join(images_dir, img_name), "rb") as f:
                plan.image.save(img_name, File(f), save=True)
            master_plans[img_name] = plan
            self.stdout.write(f"Yuklandi: {img_name} -> {plan.image.name}")

        to_create = []
        used_masters = set()
        for home in homes:
            img_name = image_files[(home.home_number - start) % cycle]
            master = master_plans[img_name]
            if master.pk not in used_masters:
                master.home = home
                master.save(update_fields=["home"])
                used_masters.add(master.pk)
            else:
                to_create.append(FloorPlan(home=home, image=master.image.name))

        FloorPlan.objects.bulk_create(to_create)

        for master in master_plans.values():
            if master.pk not in used_masters:
                master.delete()

        self.stdout.write(self.style.SUCCESS(f"Natija: {len(to_create) + len(used_masters)} ta floor plan qo'shildi"))
