import os
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from booking.models import Booking, Company
from client.models import Client
from home.models import Home
from home.services.home import HomeService

User = get_user_model()

STATUS_MAP = {
    'sotildi': Home.HomeStatus.SOLD,
    'shartnoma': Home.HomeStatus.RESERVED,
    "bo'sh": Home.HomeStatus.AVAILABLE,
    'bosh': Home.HomeStatus.AVAILABLE,
}


def fmt_phone(value):
    if not value:
        return None
    digits = str(int(value)) if isinstance(value, float) else str(value).strip()
    digits = digits.replace('+', '').replace(' ', '')
    if digits.startswith('998'):
        return f'+{digits}'
    return f'+998{digits}'


def to_str(value):
    if value is None:
        return None
    if isinstance(value, float):
        return str(int(value))
    s = str(value).strip()
    return s or None


def parse_deadline(value):
    if not value:
        return None
    s = str(value).strip()
    if not s or s == ' ':
        return None
    for fmt in ('%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
        try:
            return pd.to_datetime(s, format=fmt).date()
        except Exception:
            pass
    return None


class Command(BaseCommand):
    help = 'Import bookings from booking.xlsx'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', default='booking.xlsx', help='Excel fayl nomi (default: booking.xlsx)')

    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, kwargs['file'])

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Fayl topilmadi: {file_path}'))
            return

        df = pd.read_excel(file_path)
        df = df.where(pd.notna(df), None)

        company = Company.objects.order_by('id').first()
        if not company:
            self.stdout.write(self.style.ERROR('Company topilmadi, avval company yarating.'))
            return

        created = skipped = errors = 0

        for idx, row in df.iterrows():
            row_num = idx + 2
            try:
                self._import_row(row, company, row_num)
                created += 1
            except SkipRow as e:
                self.stdout.write(self.style.WARNING(f'  [{row_num}] skip: {e}'))
                skipped += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [{row_num}] xato: {e}'))
                errors += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nNatija: {created} yaratildi, {skipped} skip, {errors} xato'
        ))

    @transaction.atomic
    def _import_row(self, row, company, row_num):
        raw_home_num = row.get('home_number')
        if not raw_home_num:
            raise SkipRow('home_number yo`q')

        home_number = int(raw_home_num)
        map_key = to_str(row.get('map_key'))

        bino = row.get('Bino')
        home = None
        if bino is not None:
            block_title = str(int(bino)) if isinstance(bino, float) else str(bino).strip()
            home = Home.objects.filter(home_number=home_number, blocks__title=block_title).first()

        if not home:
            home = Home.objects.filter(home_number=home_number).first()

        if not home:
            raise SkipRow(f'home_number={home_number}, bino={bino} topilmadi')

        if Booking.objects.filter(home=home).exists():
            raise SkipRow(f'home_number={home_number} (entrance={home.entrance}) uchun booking allaqachon mavjud')

        raw_status = str(row.get('home_status') or '').strip()
        new_status = STATUS_MAP.get(raw_status.lower())
        if not new_status:
            raise SkipRow(f'noma`lum status: "{raw_status}"')

        locked_by_name = str(row.get('locked_by') or '').strip()
        user = None
        if locked_by_name:
            user = User.objects.filter(full_name__iexact=locked_by_name).first()
            if not user:
                parts = locked_by_name.split()
                if len(parts) >= 2:
                    user = User.objects.filter(full_name__iexact=' '.join(reversed(parts))).first()
            if not user:
                self.stdout.write(self.style.WARNING(
                    f'  [{row_num}] user topilmadi: "{locked_by_name}"'
                ))

        phone = fmt_phone(row.get('phone_number'))
        phone2 = fmt_phone(row.get('phone_number2'))
        full_name = str(row.get('client_full_name') or '').strip()

        if not full_name:
            raise SkipRow('client_full_name yo`q')

        passport_date = parse_deadline(row.get('passport berilgan sana'))

        client, created = Client.objects.get_or_create(
            full_name=full_name,
            defaults={
                'phone_number': phone or '+998000000000',
                'phone_number2': phone2,
                'passport': str(row.get('passport') or '').strip() or '',
                'passport_date': passport_date,
                'address': str(row.get('address') or '').strip() or '',
            }
        )

        if not created and passport_date and client.passport_date != passport_date:
            client.passport_date = passport_date
            client.save(update_fields=['passport_date'])

        try:
            cash_payment = float(row.get('cash_payment') or 0)
        except (ValueError, TypeError):
            cash_payment = 0

        deadline = parse_deadline(row.get('deadline'))

        Booking.objects.create(
            home=home,
            client=client,
            company=company,
            cash_payment=cash_payment,
            booking_no=to_str(row.get('booking_no')),
            map_key=map_key,
            from_who=str(row.get('from_who') or '').strip() or None,
            description=str(row.get('description') or '').strip() or None,
            deadline=deadline,
        )

        HomeService.change_status(home_id=home.id, new_status=new_status, user=user, client=client)

        self.stdout.write(f'  [{row_num}] OK home={home_number} kirish={home.entrance} | {full_name} | {raw_status}')


class SkipRow(Exception):
    pass
