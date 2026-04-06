import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from home.models import Home, FloorPlan


class Command(BaseCommand):
    help = "Barcha homelarga floorplan qo‘shadi"

    def handle(self, *args, **kwargs):
        image_path = os.path.join(settings.BASE_DIR, 'data', 'genplan.png')

        with open(image_path, 'rb') as f:
            image_data = f.read()

        homes = Home.objects.all()

        for home in homes:
            if not home.plans.exists():
                FloorPlan.objects.create(home=home, image=ContentFile(image_data, name='floor.png'))

        self.stdout.write(self.style.SUCCESS("Tugadi ✅"))
