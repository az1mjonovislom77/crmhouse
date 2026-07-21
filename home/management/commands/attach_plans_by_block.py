import os
import re

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from home.models import FloorPlan, Home
from projects.models.project_models import Block

IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.webp', '.heic', '.heif')

# Rasm nomining boshidagi harflar (token) -> qaysi block(lar)dagi barcha homelarga qo'shiladi.
# Fayllar token bo'yicha guruhlanadi: "a (1).png" -> a, "b.png" -> b, "bv.png" -> bv, "v (2).png" -> v.
DEFAULT_RULES = {
    'a': ['Block - A'],
    'b': ['Block - B'],
    'v': ['Block - V'],
    'bv': ['Block - B', 'Block - V'],
}


class Command(BaseCommand):
    help = (
        "Rasm nomining boshidagi harf (token) bo'yicha guruhlab, tegishli block(lar)dagi "
        "BARCHA homelarga floor plan qilib qo'shadi. Bir guruhdagi hamma rasm har bir homega ulanadi.\n"
        "Standart qoidalar: a -> Block - A, b -> Block - B, v -> Block - V, bv -> Block - B + Block - V.\n"
        "Misol: python manage.py attach_plans_by_block --org \"Qamashi Xonadonlar\" --images-dir ."
    )

    def add_arguments(self, parser):
        parser.add_argument('--org', default='Qamashi Xonadonlar', help='Organization nomi')
        parser.add_argument(
            '--images-dir', default='.',
            help='Rasmlar papkasi (BASE_DIR ga nisbatan). Ildiz uchun: .')
        parser.add_argument(
            '--entrance', default='all',
            help="Podyezd filtri: raqam yoki all (standart all — barcha podyezdlar)")
        parser.add_argument('--clear', action='store_true',
                            help="Avval shu homelardagi mavjud floor planlarni o'chirish")
        parser.add_argument('--dry-run', action='store_true',
                            help="Bazaga yozmasdan faqat rejani ko'rsatish")

    def handle(self, *args, **options):
        org_name = options['org']
        entrance = options['entrance']
        dry_run = options['dry_run']

        images_dir = os.path.join(settings.BASE_DIR, options['images_dir'])
        if not os.path.isdir(images_dir):
            self.stdout.write(self.style.ERROR(f'Papka topilmadi: {images_dir}'))
            return

        # entrance filtri
        entrance_val = None
        if str(entrance).lower() != 'all':
            try:
                entrance_val = int(entrance)
            except (TypeError, ValueError):
                self.stdout.write(self.style.ERROR(f'--entrance noto\'g\'ri: "{entrance}" (raqam yoki "all")'))
                return

        # Fayllarni token bo'yicha guruhlash
        groups = {}
        for fname in sorted(os.listdir(images_dir)):
            if not fname.lower().endswith(IMAGE_EXTS):
                continue
            m = re.match(r'^([A-Za-z]+)', fname)
            if not m:
                continue
            token = m.group(1).lower()
            if token in DEFAULT_RULES:
                groups.setdefault(token, []).append(fname)

        if not groups:
            self.stdout.write(self.style.ERROR(
                f'{images_dir} ichida qoidalarga mos rasm topilmadi (kutilgan tokenlar: {list(DEFAULT_RULES)})'))
            return

        # Har bir qoida bo'yicha (home, fayl) juftliklarini yig'amiz
        assignments = []          # (home, fname)
        affected_homes = {}       # home.pk -> home
        unique_files = set()
        plan_lines = []

        for token, block_titles in DEFAULT_RULES.items():
            files = groups.get(token)
            if not files:
                continue

            blocks = list(Block.objects.filter(title__in=block_titles))
            found_titles = {b.title for b in blocks}
            missing_titles = [t for t in block_titles if t not in found_titles]
            if missing_titles:
                self.stdout.write(self.style.WARNING(
                    f'  "{token}" uchun block topilmadi: {missing_titles} (o\'tkazib yuborildi shu qism)'))
            if not blocks:
                continue

            homes_qs = Home.objects.filter(blocks__in=blocks, organization__name=org_name)
            if entrance_val is not None:
                homes_qs = homes_qs.filter(entrance=entrance_val)
            homes = list(homes_qs.order_by('home_number').distinct())

            plan_lines.append(
                f'  [{token}] -> {sorted(found_titles)}: {len(homes)} ta home, rasmlar: {files}')

            for home in homes:
                affected_homes[home.pk] = home
                for fname in files:
                    assignments.append((home, fname))
                    unique_files.add(fname)

        if not assignments:
            self.stdout.write(self.style.ERROR('Hech qanday home topilmadi — hech narsa qo\'shilmadi.'))
            self.stdout.write('\n'.join(plan_lines))
            return

        self.stdout.write(f'Reja (org: {org_name}, entrance: {entrance}):')
        self.stdout.write('\n'.join(plan_lines))
        self.stdout.write(self.style.SUCCESS(
            f'Jami: {len(affected_homes)} ta home, {len(assignments)} ta floor plan qo\'shiladi.'))

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry-run: bazaga hech narsa yozilmadi.'))
            return

        if options['clear']:
            deleted, _ = FloorPlan.objects.filter(home__in=list(affected_homes.values())).delete()
            self.stdout.write(self.style.WARNING(f'{deleted} ta mavjud floor plan o\'chirildi'))

        # Har bir rasmni bir marta yuklaymiz (save() webp ga optimizatsiya qiladi),
        # keyin barcha homelarga shu faylning nomini ulaymiz.
        masters = {}   # fname -> FloorPlan (image saqlangan)
        for fname in sorted(unique_files):
            plan = FloorPlan()
            with open(os.path.join(images_dir, fname), 'rb') as f:
                plan.image.save(fname, File(f), save=True)
            masters[fname] = plan
            self.stdout.write(f'Yuklandi: {fname} -> {plan.image.name}')

        used_masters = set()
        to_create = []
        for home, fname in assignments:
            master = masters[fname]
            if master.pk not in used_masters:
                # birinchi ishlatilishda masterning o'zini shu homega biriktiramiz
                master.home = home
                master.save(update_fields=['home'])
                used_masters.add(master.pk)
            else:
                to_create.append(FloorPlan(home=home, image=master.image.name))

        FloorPlan.objects.bulk_create(to_create)

        # Ishlatilmagan master qolsa (masalan homelar bo'lmasa), egasiz qoldirmaymiz
        for master in masters.values():
            if master.pk not in used_masters:
                master.delete()

        self.stdout.write(self.style.SUCCESS(
            f'Natija: {len(to_create) + len(used_masters)} ta floor plan qo\'shildi '
            f'({len(affected_homes)} ta homega).'))