import os
import sys
import django
from django.conf import settings
from django.core.files import File
from django.db import transaction
from home.models import FloorPlan, Home
from projects.models.project_models import Block

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

IMG_NAME = '1-uy 0.jpg'
BLOCK_TITLE = '1 - Block'


def main():
    img_path = os.path.join(settings.BASE_DIR, 'images', IMG_NAME)
    if not os.path.exists(img_path):
        sys.exit(f"Rasm topilmadi: {img_path}")

    block = Block.objects.filter(title=BLOCK_TITLE).first()
    if block is None:
        sys.exit(f"Blok topilmadi: {BLOCK_TITLE}")

    homes = Home.objects.filter(blocks=block).exclude(plans__isnull=False).order_by('home_number')
    if not homes.exists():
        print('Barcha uylarda plan allaqachon mavjud, hech narsa qilinmadi.')
        return

    with transaction.atomic():
        master = FloorPlan()
        with open(img_path, 'rb') as f:
            master.image.save(IMG_NAME, File(f), save=True)

        plans = [FloorPlan(home=h, image=master.image.name) for h in homes]
        FloorPlan.objects.bulk_create(plans)
        FloorPlan.objects.filter(pk=master.pk).delete()

    print(f"Qo'shildi: {len(plans)} ta uyga {IMG_NAME}")


if __name__ == '__main__':
    main()
