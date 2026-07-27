import os

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from home.models import FloorPlan, Home
from projects.models.project_models import Block


class Command(BaseCommand):
    help = (
        "Organization + Block + entrance bo'yicha homelarga rasmlarni cycling tartibida ulaydi.\n"
        "home_number 1 -> 1-rasm, 2 -> 2-rasm, ... , ro'yxat tugagach yana boshidan.\n"
        "Standart: Qamashi Xonadonlar / Block - B / entrance 1 / b1.png,b2.png,b3.png,b4.jpg\n"
        "Misol: python manage.py attach_block_plans "
        '--org "Qamashi Xonadonlar" --block "Block - B" --entrance 1 '
        "--images-dir . --order b1.png,b2.png,b3.png,b4.jpg"
    )

    def add_arguments(self, parser):
        parser.add_argument("--org", default="Qamashi Xonadonlar", help="Organization nomi")
        parser.add_argument("--block", default="Block - B", help="Block title")
        parser.add_argument("--entrance", default="1", help="Podyezd (entrance) raqami. Barcha podyezdlar uchun: all")
        parser.add_argument(
            "--start",
            default="",
            help="Ro'yxatdagi 1-rasmni oladigan home_number. Bo'sh bo'lsa guruhdagi eng kichik home_number olinadi",
        )
        parser.add_argument("--images-dir", default=".", help="Rasmlar papkasi (BASE_DIR ga nisbatan). Ildiz uchun: .")
        parser.add_argument(
            "--order",
            default="b1.png,b2.png,b3.png,b4.jpg",
            help="Rasmlar tartibi (vergul bilan): 1-home shu ro'yxatdagi 1-rasmni oladi va hokazo",
        )
        parser.add_argument(
            "--clear", action="store_true", help="Avval shu homelardagi mavjud floor planlarni o'chirish"
        )
        parser.add_argument("--dry-run", action="store_true", help="Bazaga yozmasdan faqat rejani ko'rsatish")

    def handle(self, *args, **options):
        org_name = options["org"]
        block_title = options["block"]
        entrance = options["entrance"]
        dry_run = options["dry_run"]

        try:
            block = Block.objects.get(title=block_title)
        except Block.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Block topilmadi: "{block_title}"'))
            self.stdout.write("Mavjud blocklar: " + ", ".join(Block.objects.values_list("title", flat=True)))
            return
        except Block.MultipleObjectsReturned:
            self.stdout.write(self.style.ERROR(f'"{block_title}" nomli bir nechta block bor, aniqroq kiriting'))
            return

        images_dir = os.path.join(settings.BASE_DIR, options["images_dir"])
        image_files = [name.strip() for name in options["order"].split(",") if name.strip()]
        if not image_files:
            self.stdout.write(self.style.ERROR("--order bo'sh: kamida bitta rasm nomi kerak"))
            return

        missing = [name for name in image_files if not os.path.exists(os.path.join(images_dir, name))]
        if missing:
            self.stdout.write(self.style.ERROR(f"Rasm topilmadi ({images_dir}): {missing}"))
            return

        homes_qs = Home.objects.filter(blocks=block, organization__name=org_name)
        entrance_label = "barcha podyezdlar"
        if str(entrance).lower() != "all":
            try:
                homes_qs = homes_qs.filter(entrance=int(entrance))
                entrance_label = f"entrance={int(entrance)}"
            except (TypeError, ValueError):
                self.stdout.write(self.style.ERROR(f'--entrance noto\'g\'ri: "{entrance}" (raqam yoki "all")'))
                return

        homes = list(homes_qs.order_by("home_number"))
        if not homes:
            self.stdout.write(
                self.style.ERROR(f'"{org_name}" + "{block_title}" + {entrance_label} bo\'yicha home topilmadi')
            )
            return

        cycle = len(image_files)

        if str(options["start"]).strip():
            try:
                start_num = int(options["start"])
            except (TypeError, ValueError):
                self.stdout.write(self.style.ERROR(f"--start noto'g'ri: \"{options['start']}\" (raqam bo'lishi kerak)"))
                return
        else:
            start_num = homes[0].home_number

        def image_for(home):
            return image_files[(home.home_number - start_num) % cycle]

        self.stdout.write(
            f"{len(homes)} ta home topildi ({org_name} / {block_title} / {entrance_label}). "
            f"start={start_num}, rasmlar tartibi: {image_files}"
        )

        for home in homes:
            self.stdout.write(f"  home_number={home.home_number} (id={home.pk}) -> {image_for(home)}")

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
            img_name = image_for(home)
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
