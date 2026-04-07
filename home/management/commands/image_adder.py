from django.core.management.base import BaseCommand
from django.core.files import File
from home.models import FloorPlan, Home
from projects.models.project_models import Blocks


class Command(BaseCommand):
    help = "Bulk add floor plan to homes (by block and floor range)"

    def add_arguments(self, parser):
        parser.add_argument('--block', type=str, required=True, help='Block name (A-2)')
        parser.add_argument('--from_floor', type=int, required=True)
        parser.add_argument('--to_floor', type=int, required=True)
        parser.add_argument('--image_path', type=str, required=True)

    def handle(self, *args, **options):
        block_name = options['block']
        from_floor = options['from_floor']
        to_floor = options['to_floor']
        image_path = options['image_path']

        try:
            block = Blocks.objects.get(name=block_name)
        except Blocks.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Block {block_name} topilmadi"))
            return

        homes = Home.objects.filter(blocks=block, floor__number__gte=from_floor, floor__number__lte=to_floor)

        if not homes.exists():
            self.stdout.write(self.style.WARNING("Home lar topilmadi"))
            return

        created_count = 0

        with open(image_path, "rb") as img:
            for home in homes:
                FloorPlan.objects.create(home=home, image=File(img, name=image_path.split("/")[-1]))

                img.seek(0)
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"{created_count} ta FloorPlan qo‘shildi ✅"))
