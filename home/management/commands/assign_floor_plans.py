import os

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from home.models import FloorPlan, Home
from projects.models.project_models import Block

ALLOWED_EXT = ('.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif')


class Command(BaseCommand):
    help = (
        'images/ papkasidan rasmlar olib FloorPlan yaratadi va block homelariga cycling tartibida bog\'laydi.\n'
        'Misol: python manage.py assign_floor_plans --block-title "3-block" --prefix "3-uy"\n'
        '       python manage.py assign_floor_plans --block 2 --prefix "3-uy" --count 4'
    )

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--block', type=int, help='Block ID (masalan: 2)')
        group.add_argument('--block-title', type=str, help='Block nomi (masalan: "3-block")')

        parser.add_argument('--images-dir', default='images', help='Rasmlar papkasi (default: images)')
        parser.add_argument(
            '--prefix', type=str, default='',
            help='Rasm fayl nomlarini filtrlash uchun prefix (masalan: "3-uy"). '
                 'Bo\'sh qoldirilsa barcha rasmlar olinadi.'
        )
        parser.add_argument(
            '--count', type=int, default=0,
            help='Nechta rasm ishlatish (default: 0 = barchasi). Masalan: --count 4'
        )
        parser.add_argument('--clear', action='store_true', help='Avval mavjud floor planlarni o\'chirish')

    def handle(self, *args, **kwargs):
        # Block aniqlash
        if kwargs['block_title']:
            try:
                block = Block.objects.get(title=kwargs['block_title'])
            except Block.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Block topilmadi: "{kwargs["block_title"]}"'))
                return
            block_filter = {'blocks': block}
            block_label = f'"{block.title}" (id={block.id})'
        else:
            block_id = kwargs['block']
            try:
                block = Block.objects.get(id=block_id)
            except Block.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Block topilmadi: id={block_id}'))
                return
            block_filter = {'blocks': block}
            block_label = f'id={block_id} ("{block.title}")'

        images_dir = os.path.join(settings.BASE_DIR, kwargs['images_dir'])
        prefix = kwargs['prefix']
        max_count = kwargs['count']
        clear = kwargs['clear']

        if not os.path.exists(images_dir):
            self.stdout.write(self.style.ERROR(f'Papka topilmadi: {images_dir}'))
            return

        # Rasmlarni filter va sort qilish
        image_files = sorted([
            f for f in os.listdir(images_dir)
            if f.lower().endswith(ALLOWED_EXT)
            and (not prefix or f.startswith(prefix))
        ])

        if not image_files:
            msg = f'Rasm topilmadi: {images_dir}'
            if prefix:
                msg += f' (prefix="{prefix}")'
            self.stdout.write(self.style.ERROR(msg))
            return

        if max_count and max_count > 0:
            image_files = image_files[:max_count]

        cycle_size = len(image_files)
        self.stdout.write(f'Rasmlar ({images_dir}){f" [prefix={prefix}]" if prefix else ""}: {image_files}')
        self.stdout.write(f'Cycling: {cycle_size} ta rasm bilan')

        # FloorPlan master obyektlarini yaratish
        master_plans = []
        for img_name in image_files:
            img_path = os.path.join(images_dir, img_name)
            plan = FloorPlan()
            with open(img_path, 'rb') as f:
                plan.image.save(img_name, File(f), save=True)
            master_plans.append(plan)
            self.stdout.write(f'  Saqlandi: {img_name} → {plan.image.name}')

        # Block homelarini olish
        homes = list(Home.objects.filter(**block_filter).order_by('home_number'))
        if not homes:
            self.stdout.write(self.style.ERROR(f'Block {block_label} da home topilmadi'))
            for p in master_plans:
                p.delete()
            return

        self.stdout.write(f'\nBlock {block_label}: {len(homes)} ta home topildi')

        if clear:
            deleted, _ = FloorPlan.objects.filter(home__in=homes).delete()
            self.stdout.write(self.style.WARNING(f'  {deleted} ta mavjud floor plan o\'chirildi'))

        # Har bir home ga cycling tartibda floor plan yaratish
        to_create = []
        for i, home in enumerate(homes):
            idx = i % cycle_size
            plan = master_plans[idx]
            to_create.append(FloorPlan(home=home, image=plan.image.name))
            self.stdout.write(f'  home_number={home.home_number} → {image_files[idx]}')

        FloorPlan.objects.bulk_create(to_create)

        self.stdout.write(self.style.SUCCESS(
            f'\nNatija: {len(to_create)} ta floor plan yaratildi '
            f'({cycle_size} ta rasm cycling tartibida)'
        ))
