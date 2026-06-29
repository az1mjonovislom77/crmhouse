import warnings
import openpyxl
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Excel dagi o\'tkazilgan qatorlarni tahlil qiladi'

    def add_arguments(self, parser):
        parser.add_argument('--file', default='lead.xlsx')

    def handle(self, *args, **options):
        warnings.filterwarnings('ignore')
        if hasattr(self.stdout, 'reconfigure'):
            try:
                self.stdout.reconfigure(encoding='utf-8')
            except Exception:
                pass

        wb = openpyxl.load_workbook(options['file'])
        ws = wb.active

        total = 0
        skipped_both_empty = 0
        skipped_no_name = 0
        skipped_no_phone = 0
        has_data = 0
        formula_id = 0
        completely_empty = 0

        examples_skipped = []

        for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            total += 1
            _, full_name, phone, source, subsidiya, status, manager, *rest = row

            all_none = all(v is None for v in row)
            if all_none:
                completely_empty += 1
                continue

            if not full_name and not phone:
                skipped_both_empty += 1
                if len(examples_skipped) < 10:
                    examples_skipped.append((row_num, row[:7]))
                continue

            has_data += 1
            if not full_name:
                skipped_no_name += 1
            if not phone:
                skipped_no_phone += 1

        self.stdout.write(f'Jami qatorlar (header siz): {total}')
        self.stdout.write(f'To\'liq bo\'sh qatorlar:      {completely_empty}')
        self.stdout.write(f'Ism+Telefon ikkalasi yo\'q:  {skipped_both_empty}')
        self.stdout.write(f'Ma\'lumotli qatorlar:        {has_data}')
        self.stdout.write(f'  - Ismsiz (telefon bor):   {skipped_no_name}')
        self.stdout.write(f'  - Telefonsiz (ism bor):   {skipped_no_phone}')

        if examples_skipped:
            self.stdout.write('\n=== O\'TKAZILGAN QATORLAR (birinchi 10 ta) ===')
            for row_num, vals in examples_skipped:
                self.stdout.write(f'  Row {row_num}: {list(vals)}')
