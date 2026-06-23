import os

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from home.models import FloorPlan, Home

ALLOWED_EXT = ('.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif')


class Command(BaseCommand):
    help = 'images/ papkasidan 3 ta rasm olib FloorPlan yaratadi va block homelariga 1-2-3 tartibida bog\'laydi'

    def add_arguments(self, parser):
        parser.add_argument('--block', type=int, default=2, help='Block ID (default: 2)')
        parser.add_argument('--images-dir', default='images', help='Rasmlar papkasi (default: images)')
        parser.add_argument('--clear', action='store_true', help='Avval mavjud floor planlarni o\'chirish')

    def handle(self, *args, **kwargs):
        block_id = kwargs['block']
        clear = kwargs['clear']
        images_dir = os.path.join(settings.BASE_DIR, kwargs['images_dir'])

        if not os.path.exists(images_dir):
            self.stdout.write(self.style.ERROR(f'Papka topilmadi: {images_dir}'))
            return

        image_files = sorted([
            f for f in os.listdir(images_dir)
            if f.lower().endswith(ALLOWED_EXT)
        ])

        if len(image_files) < 3:
            self.stdout.write(self.style.ERROR(
                f'Kamida 3 ta rasm kerak, papkada topildi: {len(image_files)}'
            ))
            return

        image_files = image_files[:3]
        self.stdout.write(f'Rasmlar ({images_dir}): {image_files}')

        # 3 ta rasmni media ga saqlash (webp ga o'tkazish ham shu yerda bo'ladi)
        master_plans = []
        for img_name in image_files:
            img_path = os.path.join(images_dir, img_name)
            plan = FloorPlan()
            with open(img_path, 'rb') as f:
                plan.image.save(img_name, File(f), save=True)
            master_plans.append(plan)
            self.stdout.write(f'  Saqlandi: {img_name} → {plan.image.name}')

        # Block homelarini olish
        homes = list(Home.objects.filter(blocks_id=block_id).order_by('home_number'))
        if not homes:
            self.stdout.write(self.style.ERROR(f'Block {block_id} da home topilmadi'))
            for p in master_plans:
                p.delete()
            return

        self.stdout.write(f'\nBlock {block_id}: {len(homes)} ta home topildi')

        if clear:
            deleted, _ = FloorPlan.objects.filter(home__blocks_id=block_id).delete()
            self.stdout.write(self.style.WARNING(f'  {deleted} ta mavjud floor plan o\'chirildi'))

        # Har bir home ga cycling tartibda floor plan yaratish
        to_create = []
        for i, home in enumerate(homes):
            plan = master_plans[i % 3]
            to_create.append(FloorPlan(home=home, image=plan.image.name))
            self.stdout.write(f'  home_number={home.home_number} → {image_files[i % 3]}')

        FloorPlan.objects.bulk_create(to_create)

        self.stdout.write(self.style.SUCCESS(
            f'\nNatija: {len(to_create)} ta floor plan yaratildi (1-2-3 tartibida)'
        ))
