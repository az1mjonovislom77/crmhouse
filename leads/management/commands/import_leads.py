import re
import warnings
from datetime import datetime

import openpyxl
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from leads.models import Lead, LeadEvent

User = get_user_model()

# Haqiqiy menejer emasligi aniq bo'lgan qatorlar
FAKE_MANAGERS = {"sms junatildi o'chirilgan", "sms junatildi uchirilgan"}

# ---------- Mapping jadvallar ----------

STATUS_MAP = {
    'Murojaat qildi':         ('yangi_murojaat',  'murojaat_qildi'),
    "Ko'rdi / Eshitdi":       ('yangi_murojaat',  'kordi_eshitdi'),
    "Atkaz (Ko'rdi/Eshitdi)": ('bekor_qilingan',  'atkaz_qildi'),
    'Atkaz qildi':            ('bekor_qilingan',  'atkaz_qildi'),
    'Uchrashuv belgilandi':   ('uchrashuv',        'uchrashuv_belgilandi'),
    'Keldi':                  ('uchrashuv',        'keldi'),
    'Shartnoma qildi':        ('jarayon',          'shartnoma_qildi'),
    'Uy oldi':                ('muvaffaqiyatli',   'uy_oldi'),
}

SOURCE_MAP = {
    'Instagram':      'Instagram',
    'Telegram':       'Telegram',
    'Reklama':        'Reklama',
    'SUHROB_Reklama': 'Reklama',
    'Tavsiya':        'Tavsiya',
    "O'zi kelgan":    'Boshqa',
    "Noma'lum":       'Boshqa',
}

# [DD.MM.YYYY; HH:MM | Ism] 💬 matn
COMMENT_RE = re.compile(
    r'\[(\d{2}\.\d{2}\.\d{4});\s*(\d{2}:\d{2})\s*\|\s*([^\]]+)\]\s*💬\s*(.+?)(?=\n\[|\Z)',
    re.DOTALL,
)

# ---------- Yordamchi funksiyalar ----------

def normalize(val):
    """Uzbek apostrof variantlarini standart belgiga o'tkazadi."""
    if not val:
        return ''
    s = str(val).strip()
    for ch in ('‘', '’', 'ʼ', '￼', '`', '´'):
        s = s.replace(ch, "'")
    return s


def clean_phone(val):
    if not val:
        return "Noma'lum"
    phone = str(val).split('\n')[0].strip()
    phone = re.sub(r'[^\d+]', '', phone)
    return phone[:30] if phone else "Noma'lum"


def parse_subsidiya(val):
    return str(val).strip() in ('Bor', 'Jarayonda') if val else False


def make_aware(dt):
    if isinstance(dt, datetime):
        return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
    if isinstance(dt, str):
        dt = dt.strip()
        for fmt in ('%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y'):
            try:
                return timezone.make_aware(datetime.strptime(dt, fmt))
            except ValueError:
                continue
    return None


def parse_comments(text):
    """Structured commentlarni ajratadi, qolgan matnni qaytaradi."""
    if not text:
        return [], ''
    matches = COMMENT_RE.findall(str(text))
    remaining = COMMENT_RE.sub('', str(text)).strip()
    return matches, remaining


def create_comment_event(lead, text, by, at=None):
    """TYPE_COMMENT event yaratadi, ixtiyoriy sanani backdate qiladi."""
    ev = LeadEvent.objects.create(
        lead=lead,
        type=LeadEvent.TYPE_COMMENT,
        text=text,
        by=by,
    )
    if at:
        LeadEvent.objects.filter(pk=ev.pk).update(at=at)
    return ev


# ---------- Asosiy command ----------

class Command(BaseCommand):
    help = 'lead.xlsx dan Lead va LeadEvent larni import qiladi'

    def add_arguments(self, parser):
        parser.add_argument('--file', default='lead.xlsx', help="Excel fayl yo'li")
        parser.add_argument('--dry-run', action='store_true', help='Bazaga yozmasdan tekshirish')
        parser.add_argument('--reset', action='store_true', help='Import oldidan barcha leadlarni o\'chiradi')

    def handle(self, *args, **options):
        warnings.filterwarnings('ignore')
        if hasattr(self.stdout, 'reconfigure'):
            try:
                self.stdout.reconfigure(encoding='utf-8')
                self.stderr.reconfigure(encoding='utf-8')
            except Exception:
                pass

        filepath = options['file']
        dry_run = options['dry_run']

        if options['reset'] and not dry_run:
            deleted, _ = Lead.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'{deleted} ta lead o\'chirildi'))

        # full_name → User mapping (katta-kichik harf farqsiz)
        users = {u.full_name.strip().lower(): u for u in User.objects.all()}

        # Topilmagan menejerlarni hisoblaymiz
        unmatched: dict[str, int] = {}

        # Bazada mavjud phone raqamlar — duplicate oldini olish uchun
        existing_phones = set(Lead.objects.values_list('phone', flat=True))

        wb = openpyxl.load_workbook(filepath)
        ws = wb.active

        created_count = 0
        skipped_count = 0
        duplicate_count = 0
        error_count = 0

        for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            full_name    = row[1]
            phone        = row[2]
            source_raw   = row[3]
            subsidiya_raw = row[4]
            status_raw   = row[5]
            manager_name = row[6]
            meeting_col  = row[7]
            note_raw     = row[8]
            contact_date = row[9] if len(row) > 9 else None

            if not full_name and not phone:
                skipped_count += 1
                continue

            try:
                full_name = str(full_name).strip() if full_name else "Noma'lum"
                phone = clean_phone(phone)
                source = SOURCE_MAP.get(normalize(source_raw), 'Boshqa')
                subsidiya = parse_subsidiya(subsidiya_raw)

                status_key = normalize(status_raw)
                status, sub_status = STATUS_MAP.get(
                    status_key, ('yangi_murojaat', 'murojaat_qildi')
                )

                manager_key = normalize(manager_name)
                if manager_key and manager_key not in FAKE_MANAGERS:
                    owner = users.get(manager_key.lower())
                    if not owner:
                        unmatched[manager_key] = unmatched.get(manager_key, 0) + 1
                else:
                    owner = None

                contact_dt = make_aware(contact_date) if isinstance(contact_date, datetime) else None

                # --- "Uchrashuv belgilandi" ustuni ---
                # datetime bo'lsa → meeting_at, matn bo'lsa → alohida event
                if isinstance(meeting_col, datetime):
                    meeting_at = make_aware(meeting_col)
                    uchrashuv_note = None
                elif meeting_col:
                    meeting_at = None
                    uchrashuv_note = str(meeting_col).strip() or None
                else:
                    meeting_at = None
                    uchrashuv_note = None

                # --- "Umumiy ma'lumot" ustuni ---
                # Structured [sana|ism] 💬 matn va qolgan oddiy matn
                structured_comments, general_note = parse_comments(note_raw)

                # Bazada bu phone bor bo'lsa — faqat contacted_at ni yangilaymiz
                if phone in existing_phones:
                    if contact_dt:
                        Lead.objects.filter(phone=phone, contacted_at__isnull=True).update(
                            contacted_at=contact_dt
                        )
                    duplicate_count += 1
                    continue

                if dry_run:
                    ev_count = (
                        1  # created
                        + (1 if meeting_at else 0)
                        + (1 if uchrashuv_note else 0)
                        + (1 if general_note else 0)
                        + len(structured_comments)
                    )
                    self.stdout.write(
                        f'[{row_num}] {full_name} | {status}/{sub_status} '
                        f'| uchrashuv_note={"ha" if uchrashuv_note else "yoq"} '
                        f'| general_note={"ha" if general_note else "yoq"} '
                        f'| struct_comments={len(structured_comments)} '
                        f'| jami_events={ev_count}'
                    )
                    created_count += 1
                    continue

                # Lead yaratish va phone ni existing ga qo'shamiz (bir fayldagi dublikat uchun)
                existing_phones.add(phone)
                lead = Lead.objects.create(
                    full_name=full_name,
                    phone=phone,
                    source=source,
                    board=Lead.BOARD_SALES,
                    status=status,
                    sub_status=sub_status,
                    owner=owner,
                    subsidiya=subsidiya,
                    note=general_note or None,
                    meeting_at=meeting_at,
                    contacted_at=contact_dt,
                    score=0,
                )

                # created_at ni asl sanaga backdate qilamiz
                if contact_dt:
                    Lead.objects.filter(pk=lead.pk).update(created_at=contact_dt)

                # Event 1: created
                ev = LeadEvent.objects.create(
                    lead=lead, type=LeadEvent.TYPE_CREATED, by=owner,
                )
                if contact_dt:
                    LeadEvent.objects.filter(pk=ev.pk).update(at=contact_dt)

                # Event 2: uchrashuv (datetime bo'lsa)
                if meeting_at:
                    LeadEvent.objects.create(
                        lead=lead,
                        type=LeadEvent.TYPE_MEETING,
                        meeting_at=meeting_at,
                        meeting_type='Ofisda',
                        by=owner,
                    )

                # Event 3: "Uchrashuv belgilandi" ustunidagi matn → alohida comment
                if uchrashuv_note:
                    create_comment_event(lead, uchrashuv_note, owner, contact_dt)

                # Event 4: "Umumiy ma'lumot" oddiy qolgan matn → alohida comment
                if general_note:
                    create_comment_event(lead, general_note, owner, contact_dt)

                # Event 5+: structured [sana|ism] 💬 commentlar
                for date_str, time_str, commentor_name, text in structured_comments:
                    try:
                        dt = datetime.strptime(f'{date_str} {time_str}', '%d.%m.%Y %H:%M')
                        dt = timezone.make_aware(dt)
                    except ValueError:
                        dt = contact_dt or timezone.now()
                    commentor = users.get(commentor_name.strip()) or owner
                    create_comment_event(lead, text.strip(), commentor, dt)

                created_count += 1

            except Exception as e:
                error_count += 1
                self.stderr.write(f'Row {row_num} xato: {e}')

        label = '[DRY RUN] ' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f'{label}Yaratildi: {created_count} | '
            f"O'tkazildi: {skipped_count} | "
            f'Dublikat: {duplicate_count} | '
            f'Xato: {error_count}'
        ))

        if unmatched:
            self.stdout.write(self.style.WARNING(
                f'\n⚠  {len(unmatched)} ta menejer DB da topilmadi '
                f'(jami {sum(unmatched.values())} ta lead owner=None):'
            ))
            for name, cnt in sorted(unmatched.items(), key=lambda x: -x[1]):
                self.stdout.write(f'   "{name}" — {cnt} ta lead')
            self.stdout.write('   → Ushbu userlarni yaratib, --reset bilan qayta ishlatib ko\'ring')
