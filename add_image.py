import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django.core.files import File
from home.models import FloorPlan, Home
from projects.models.project_models import Block

img_name = '1-uy 0.jpg'
img_path = os.path.join(settings.BASE_DIR, 'images', img_name)
block = Block.objects.get(title='1 - Block')
homes = Home.objects.filter(blocks=block).order_by('home_number')
master = FloorPlan()
master.image.save(img_name, File(open(img_path, 'rb')), save=True)
plans = [FloorPlan(home=h, image=master.image.name) for h in homes]
FloorPlan.objects.bulk_create(plans)
print(f'Qoshildi: {len(plans)} ta home ga {img_name}')
