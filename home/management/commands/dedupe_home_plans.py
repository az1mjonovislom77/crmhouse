from django.core.management.base import BaseCommand

from home.models import FloorPlan, Home
from projects.models.project_models import Block


class Command(BaseCommand):
    help = (
        "Bir xil rasm ikki marta qo'shilib qolganda, har bir homedan ENG OXIRGI qo'shilgan "
        "floor plan(lar)ni o'chiradi. Eskilariga (masalan area bo'yicha qo'shilganlarga) tegmaydi.\n"
        "Misol: python manage.py dedupe_home_plans "
        '--org "Paxtazor Xonadonlar" --block "Block - V" --from-number 73 --to-number 112 --dry-run'
    )

    def add_arguments(self, parser):
        parser.add_argument("--org", required=True, help="Organization nomi")
        parser.add_argument("--block", required=True, help="Block title")
        parser.add_argument("--from-number", type=int, help="Faqat shu home_number dan boshlab")
        parser.add_argument("--to-number", type=int, help="Faqat shu home_number gacha, o'zi ham kiradi")
        parser.add_argument(
            "--delete-newest",
            type=int,
            default=1,
            help="Har bir homedan nechta eng oxirgi planni o'chirish (default: 1)",
        )
        parser.add_argument(
            "--min-plans",
            type=int,
            default=2,
            help="Faqat shuncha yoki undan ko'p plani bor homelarga tegish (default: 2)",
        )
        parser.add_argument("--dry-run", action="store_true", help="Bazaga tegmasdan faqat rejani ko'rsatish")

    def handle(self, *args, **options):
        org_name = options["org"]
        block_title = options["block"]
        delete_newest = options["delete_newest"]
        min_plans = options["min_plans"]

        if delete_newest < 1:
            self.stdout.write(self.style.ERROR("--delete-newest kamida 1 bo'lishi kerak"))
            return

        blocks = list(Block.objects.filter(title=block_title, homes__organization__name=org_name).distinct())
        if not blocks:
            self.stdout.write(self.style.ERROR(f'"{org_name}" ichida block topilmadi: "{block_title}"'))
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

        to_delete = []
        skipped = 0
        for home in homes:
            plans = list(home.plans.order_by("pk"))
            if len(plans) < min_plans:
                skipped += 1
                self.stdout.write(f"  home_number={home.home_number}: {len(plans)} ta plan — tegilmadi")
                continue

            keep, drop = plans[:-delete_newest], plans[-delete_newest:]
            to_delete.extend(drop)
            self.stdout.write(
                f"  home_number={home.home_number}: "
                f"qoladi {[(p.pk, p.image.name) for p in keep]} | "
                f"o'chadi {[(p.pk, p.image.name) for p in drop]}"
            )

        if not to_delete:
            self.stdout.write(self.style.WARNING("O'chiriladigan plan topilmadi."))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Jami: {len(to_delete)} ta floor plan o'chiriladi "
                f"({len(homes) - skipped} ta home, {skipped} ta home tegilmadi)."
            )
        )

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry-run: bazaga hech narsa yozilmadi."))
            return

        # Faqat DB qatorlari o'chadi — media fayllarga tegilmaydi, chunki bitta fayl
        # ko'p FloorPlan qatorlari tomonidan ulashiladi (bulk_create nusxalari).
        deleted, _ = FloorPlan.objects.filter(pk__in=[p.pk for p in to_delete]).delete()
        self.stdout.write(self.style.SUCCESS(f"Natija: {deleted} ta floor plan o'chirildi."))
