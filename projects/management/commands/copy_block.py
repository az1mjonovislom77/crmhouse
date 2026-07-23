from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.db import transaction

from home.models import FloorPlan, Home, HomeStatusHistory
from projects.models.project_models import Block, BlockImage


class Command(BaseCommand):
    help = (
        "Blockni barcha homelari, block va home rasmlari bilan birga yangi nom ostida nusxalaydi.\n"
        "Rasmlar storage'da fizik nusxalanadi, yangi block eskisidan to'liq mustaqil bo'ladi.\n"
        'Misol: python manage.py copy_block --org "Qamashi Xonadonlar" '
        '--source "Block - B" --new-title "Block - D"'
    )

    def add_arguments(self, parser):
        parser.add_argument('--org', default='Qamashi Xonadonlar', help='Organization nomi')
        parser.add_argument('--source', required=True, help='Nusxalanadigan block title')
        parser.add_argument('--new-title', required=True, help='Yangi block title')
        parser.add_argument('--with-history', action='store_true',
                            help="HomeStatusHistory yozuvlarini ham nusxalash (default: nusxalanmaydi)")
        parser.add_argument('--dry-run', action='store_true',
                            help="Bazaga yozmasdan faqat rejani ko'rsatish")

    def copy_image(self, name):
        """Storage'dagi faylni nusxalab yangi nomini qaytaradi."""
        if not name:
            return ''
        if not default_storage.exists(name):
            self.stdout.write(self.style.WARNING(
                f"  Fayl storage'da topilmadi, eski yo'l bilan ulanadi: {name}"))
            return name
        with default_storage.open(name, 'rb') as f:
            data = f.read()
        return default_storage.save(name, ContentFile(data))

    def handle(self, *args, **options):
        org_name = options['org']
        source_title = options['source']
        new_title = options['new_title']
        dry_run = options['dry_run']
        with_history = options['with_history']

        qs = Block.objects.filter(title=source_title)
        if qs.count() > 1 and org_name:
            qs = qs.filter(projects__organization__name=org_name)
        if not qs.exists():
            self.stdout.write(self.style.ERROR(f'Block topilmadi: "{source_title}"'))
            self.stdout.write('Mavjud blocklar: ' + ', '.join(Block.objects.values_list('title', flat=True)))
            return
        if qs.count() > 1:
            self.stdout.write(self.style.ERROR(
                f'"{source_title}" nomli bir nechta block bor (id: '
                f'{", ".join(str(pk) for pk in qs.values_list("id", flat=True))}), aniqroq kiriting'))
            return
        src_block = qs.first()

        if Block.objects.filter(title=new_title, projects=src_block.projects).exists():
            self.stdout.write(self.style.ERROR(
                f'"{new_title}" nomli block shu projectda allaqachon mavjud, avval uni tekshiring'))
            return

        homes = list(src_block.homes.all().order_by('id'))
        block_images = list(src_block.plans.all())
        plans_count = FloorPlan.objects.filter(home__in=homes).count()
        history_count = HomeStatusHistory.objects.filter(home__in=homes).count()

        self.stdout.write(
            f'"{src_block.title}" (id={src_block.pk}, project="{src_block.projects}") -> "{new_title}"')
        self.stdout.write(
            f'  Homelar: {len(homes)}, Block rasmlari: {len(block_images)}, '
            f'Home rasmlari: {plans_count}, Status history: {history_count}'
            + ('' if with_history else ' (nusxalanmaydi)'))

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry-run: hech narsa yozilmadi'))
            return

        with transaction.atomic():
            new_block = Block.objects.create(projects=src_block.projects, title=new_title)

            BlockImage.objects.bulk_create([
                BlockImage(block=new_block, image=self.copy_image(bi.image.name))
                for bi in block_images
            ])

            new_homes = Home.objects.bulk_create([
                Home(
                    organization=h.organization,
                    home_number=h.home_number,
                    blocks=new_block,
                    floor=h.floor,
                    rooms=h.rooms,
                    area=h.area,
                    home_status=h.home_status,
                    renovation=h.renovation,
                    price_per_sqm=h.price_per_sqm,
                    entrance=h.entrance,
                ) for h in homes
            ])
            home_map = {old.pk: new for old, new in zip(homes, new_homes, strict=True)}

            new_plans = []
            for plan in FloorPlan.objects.filter(home__in=homes):
                new_plans.append(FloorPlan(
                    home=home_map[plan.home_id],
                    image=self.copy_image(plan.image.name),
                ))
            FloorPlan.objects.bulk_create(new_plans)

            if with_history:
                for old_h in HomeStatusHistory.objects.filter(home__in=homes):
                    new_h = HomeStatusHistory.objects.create(
                        client=old_h.client,
                        home=home_map[old_h.home_id],
                        from_status=old_h.from_status,
                        to_status=old_h.to_status,
                        changed_by=old_h.changed_by,
                    )
                    HomeStatusHistory.objects.filter(pk=new_h.pk).update(changed_at=old_h.changed_at)

        self.stdout.write(self.style.SUCCESS(
            f'Tayyor: "{new_title}" (id={new_block.pk}) — {len(new_homes)} home, '
            f'{len(block_images)} block rasm, {len(new_plans)} home rasm nusxalandi'))
