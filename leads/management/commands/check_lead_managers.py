import warnings
import openpyxl
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = 'Excel dagi menejerlar va DB userlari mosligini tekshiradi'

    def add_arguments(self, parser):
        parser.add_argument('--file', default='lead.xlsx')

    def handle(self, *args, **options):
        warnings.filterwarnings('ignore')
        if hasattr(self.stdout, 'reconfigure'):
            try:
                self.stdout.reconfigure(encoding='utf-8')
            except Exception:
                pass

        users_qs = User.objects.all().order_by('full_name')
        users_map = {u.full_name.strip(): u for u in users_qs}

        self.stdout.write('=== DB DAGI USERLAR ===')
        for u in users_qs:
            self.stdout.write(f'  id={u.id} | "{u.full_name}" | @{u.username}')

        wb = openpyxl.load_workbook(options['file'])
        ws = wb.active
        managers = {}
        for row in ws.iter_rows(min_row=2, values_only=True):
            m = str(row[6]).strip() if row[6] else ''
            if m:
                managers[m] = managers.get(m, 0) + 1

        self.stdout.write('\n=== EXCEL MENEJERLAR ===')
        for name, count in sorted(managers.items(), key=lambda x: -x[1]):
            matched = users_map.get(name)
            if matched:
                mark = self.style.SUCCESS(f'OK  id={matched.id}')
            else:
                mark = self.style.ERROR('TOPILMADI')
            self.stdout.write(f'  [{mark}] "{name}" — {count} ta lead')
