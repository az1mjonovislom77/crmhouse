import os
import re
from datetime import datetime, time
from decimal import Decimal, InvalidOperation

import pandas as pd
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from booking.models import Booking, Company
from client.models import Client
from home.models import Home
from home.services.home import HomeService
from organization.models import Organization

User = get_user_model()

STATUS_MAP = {
    "sotildi": Home.HomeStatus.SOLD,
    "shartnoma": Home.HomeStatus.RESERVED,
    "band": Home.HomeStatus.RESERVED,
    "bo'sh": Home.HomeStatus.AVAILABLE,
    "bosh": Home.HomeStatus.AVAILABLE,
    "kalit topshirildi": Home.HomeStatus.KALIT_TOPSHIRILDI,
    "nomiga otkazib berildi": Home.HomeStatus.NOMIGA_OTKAZIB_BERILDI,
}

COLUMN_ALIASES = {
    "home_number": ["xonadon raqami", "home_number"],
    "block": ["bino", "block", "blok"],
    "entrance": ["pod'ezd", "podezd", "kirish", "entrance"],
    "floor": ["qavat", "floor"],
    "home_status": ["status", "home_status", "holat"],
    "client_full_name": ["mijoz f.i.sh", "mijoz fish", "client_full_name"],
    "address": ["manzil", "address"],
    "passport": ["pasport", "passport"],
    "from_who": ["kim tomonidan berilgan", "from_who"],
    "passport_date": ["pasport berilgan sana", "passport_date"],
    "phone_number": ["telefon 1", "telefon", "phone_number"],
    "phone_number2": ["telefon 2", "phone_number2"],
    "contract_date": ["shartnoma sanasi", "contract_date"],
    "booking_no": ["shartnoma no", "shartnoma #", "shartnoma", "booking_no"],
    "map_key": ["mapkey", "map_key"],
    "locked_by": ["lockedby", "locked_by"],
    "deadline": ["deadline", "muddat"],
    "description": ["izoh", "description"],
    "price_per_m2": ["1 m2 narx", "1 m² narx", "price_per_m2"],
    "total_price": ["umumiy narx", "total_price", "contract_price"],
    "down_payment": ["boshlang'ich to'lov", "down_payment", "manual_down_payment"],
}

REQUIRED_COLUMNS = ("home_number", "home_status", "client_full_name")

BOOKING_MONEY_FIELDS = ("price_per_m2", "contract_price", "manual_down_payment")

PLACEHOLDER_PHONE = "+998000000000"


def norm_header(value):
    s = str(value).strip().lower()
    for ch in "’‘`´ʻʼ":
        s = s.replace(ch, "'")
    s = s.replace("№", "no").replace("²", "2")
    return re.sub(r"\s+", " ", s)


def is_blank(value):
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip() in ("", "nan", "NaT", "None")


def fmt_phone(value):
    if is_blank(value):
        return None
    digits = str(int(value)) if isinstance(value, float) else str(value).strip()
    digits = re.sub(r"\D", "", digits)
    if not digits:
        return None
    if digits.startswith("998"):
        return f"+{digits}"
    return f"+998{digits}"


def to_str(value):
    if is_blank(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    s = str(value).strip()
    return s or None


def to_decimal(value):
    if is_blank(value):
        return None
    if isinstance(value, (int, float, Decimal)):
        raw = str(value)
    else:
        raw = re.sub(r"[^\d.,-]", "", str(value)).replace(",", ".")
    try:
        return Decimal(raw).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None


def parse_date(value):
    if is_blank(value):
        return None
    if hasattr(value, "date"):
        return value.date()
    s = str(value).strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    try:
        parsed = pd.to_datetime(s, dayfirst=True)
    except Exception:
        return None
    return None if pd.isna(parsed) else parsed.date()


def differs(current, value):
    if isinstance(current, datetime) and isinstance(value, datetime):
        return current != value
    if isinstance(current, Decimal) or isinstance(value, Decimal):
        try:
            return Decimal(str(current)) != Decimal(str(value))
        except (InvalidOperation, ValueError):
            pass
    return str(current) != str(value)


class SkipRow(Exception):
    pass


class DryRunRollback(Exception):
    pass


class Command(BaseCommand):
    help = "Excel (fz.xlsx) dan mijoz + booking import qilib, uy statusini yangilaydi"

    def add_arguments(self, parser):
        parser.add_argument("--file", default="booking.xlsx", help="Excel fayl nomi (default: booking.xlsx)")
        parser.add_argument("--sheet", default=0, help="Varaq nomi yoki indeksi (default: birinchi varaq)")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Hech narsa saqlanmaydi: barcha o'zgarishlar simulyatsiya qilinib, oxirida rollback qilinadi",
        )
        parser.add_argument(
            "--block-prefix",
            default="",
            help='Blok title prefiksi, masalan "Block - " -> Bino=1 uchun "Block - 1". Default: bo`sh',
        )
        parser.add_argument(
            "--strict-block",
            action="store_true",
            help="Blok bo'yicha uy topilmasa, faqat home_number bo'yicha qidirmasin (xato uyga yozib qo'ymaslik uchun)",
        )
        parser.add_argument(
            "--org",
            default=None,
            help='Faqat shu organization nomiga bog`langan uylar import qilinadi, masalan: --org "Fayzli Xonadonlar"',
        )
        parser.add_argument("--org-id", type=int, default=None, help="Organization ID (--org o`rniga)")
        parser.add_argument("--company-id", type=int, default=None, help="Booking uchun Company ID")
        parser.add_argument(
            "--replace-client",
            action="store_true",
            help="Uyda boshqa mijozning aktiv bookingi bo`lsa, mijozni exceldagisiga almashtirsin "
            "(default: bunday qator skip qilinadi)",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Mavjud booking/client maydonlarini ham qayta yozsin (default: faqat bo`sh maydonlar to`ldiriladi)",
        )
        parser.add_argument(
            "--excel-wins",
            action="store_true",
            help="Excel yagona haqiqat manbai: prodda boshqa ma`lumot bo`lsa ham exceldagisi yoziladi "
            "(--overwrite va --replace-client ni birga yoqadi). Exceldagi bo`sh kataklar hech narsani o`chirmaydi.",
        )

    def handle(self, *args, **options):
        self.dry_run = options["dry_run"]
        excel_wins = options["excel_wins"]
        self.overwrite = options["overwrite"] or excel_wins
        self.replace_client = options["replace_client"] or excel_wins
        self.block_prefix = options["block_prefix"]
        self.strict_block = options["strict_block"]

        if excel_wins:
            self.stdout.write(
                self.style.WARNING(
                    "EXCEL-WINS: proddagi mavjud booking/mijoz ma`lumotlari exceldagisi bilan almashtiriladi "
                    "(bo`sh kataklar tegmaydi)"
                )
            )

        file_path = options["file"]
        if not os.path.isabs(file_path):
            file_path = os.path.join(settings.BASE_DIR, file_path)
        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"Fayl topilmadi: {file_path}"))
            return

        sheet = options["sheet"]
        if isinstance(sheet, str) and sheet.isdigit():
            sheet = int(sheet)

        df = pd.read_excel(file_path, sheet_name=sheet)
        colmap = self._build_colmap(df)
        if colmap is None:
            return

        try:
            self.organization = self._resolve_organization(options["org"], options["org_id"])
        except Organization.DoesNotExist as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            return

        company = self._resolve_company(options["company_id"])
        if not company:
            self.stderr.write(self.style.ERROR("Company topilmadi, avval Company yarating yoki --company-id bering."))
            return

        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN: baza o'zgartirilmaydi, oxirida rollback qilinadi\n"))

        self.stats = {
            "created": 0,
            "updated": 0,
            "status_changed": 0,
            "skipped": 0,
            "errors": 0,
            "clients_created": 0,
            "conflicts": 0,
        }

        try:
            with transaction.atomic():
                for idx, row in df.iterrows():
                    row_num = idx + 2
                    data = {key: row.get(col) for key, col in colmap.items()}
                    try:
                        self._apply_row(data, company, row_num)
                    except SkipRow as exc:
                        self.stats["skipped"] += 1
                        self.stdout.write(self.style.WARNING(f"  [{row_num}] skip: {exc}"))
                    except Exception as exc:
                        self.stats["errors"] += 1
                        self.stdout.write(self.style.ERROR(f"  [{row_num}] xato: {exc}"))

                if self.dry_run:
                    raise DryRunRollback
        except DryRunRollback:
            pass

        s = self.stats
        summary = (
            f"\nNatija: {s['created']} booking yaratildi, {s['updated']} yangilandi, "
            f"{s['clients_created']} mijoz yaratildi, {s['status_changed']} uy statusi o'zgardi, "
            f"{s['skipped']} skip, {s['errors']} xato"
        )
        self.stdout.write(self.style.SUCCESS(summary))
        if s["conflicts"]:
            if self.replace_client:
                detail = (
                    "mijoz exceldagisiga almashtirildi. Eski mijoz yozuvlari bazada qoldi (bookingsiz) — "
                    "yuqoridagi KONFLIKT loglarini saqlab qo`ying."
                )
            else:
                detail = (
                    "qatorlar o`tkazib yuborildi. Loglarni tekshiring — map_key mos kelsa bazadagi yozuv "
                    "eskirgan (--excel-wins bering), mos kelmasa uy noto`g`ri topilgan."
                )
            self.stdout.write(self.style.ERROR(f"{s['conflicts']} ta KONFLIKT: {detail}"))
        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN yakunlandi — baza o'zgarmadi."))

    def _build_colmap(self, df):
        available = {norm_header(c): c for c in df.columns}
        colmap = {}
        for key, aliases in COLUMN_ALIASES.items():
            for alias in aliases:
                col = available.get(norm_header(alias))
                if col is not None:
                    colmap[key] = col
                    break

        missing = [k for k in REQUIRED_COLUMNS if k not in colmap]
        if missing:
            self.stderr.write(self.style.ERROR(f"Excelda majburiy ustunlar topilmadi: {', '.join(missing)}"))
            self.stderr.write(f"Mavjud ustunlar: {list(df.columns)}")
            return None

        skipped_keys = sorted(set(COLUMN_ALIASES) - set(colmap))
        if skipped_keys:
            self.stdout.write(self.style.WARNING(f"Topilmagan (ixtiyoriy) ustunlar: {', '.join(skipped_keys)}"))
        return colmap

    def _resolve_organization(self, org_name, org_id):
        if org_id:
            org = Organization.objects.filter(pk=org_id).first()
            if not org:
                raise Organization.DoesNotExist(f"Organization id={org_id} topilmadi")
        elif org_name:
            org = Organization.objects.filter(name__iexact=org_name.strip()).first()
            if not org:
                names = list(Organization.objects.values_list("name", flat=True))
                raise Organization.DoesNotExist(f'Organization "{org_name}" topilmadi. Mavjudlari: {names}')
        else:
            self.stdout.write(
                self.style.WARNING(
                    "DIQQAT: organization filtri berilmadi — bazadagi BARCHA uylar bo`yicha qidiriladi. "
                    'Cheklash uchun: --org "Fayzli Xonadonlar"'
                )
            )
            return None

        home_count = Home.objects.filter(organization=org).count()
        self.stdout.write(self.style.SUCCESS(f'Organization: "{org.name}" (id={org.pk}), {home_count} ta uy\n'))
        return org

    def _resolve_company(self, company_id):
        if company_id:
            return Company.objects.filter(pk=company_id).first()
        if self.organization:
            company = Company.objects.filter(organization=self.organization).order_by("id").first()
            if company:
                return company
            self.stdout.write(
                self.style.WARNING(
                    f'"{self.organization.name}" uchun Company topilmadi — birinchi mavjud Company olinadi'
                )
            )
        return Company.objects.order_by("id").first()

    def _find_home(self, data, row_num):
        raw_number = data.get("home_number")
        if is_blank(raw_number):
            raise SkipRow("xonadon raqami yo`q")
        home_number = int(float(raw_number))

        qs = Home.objects.select_related("blocks__projects", "floor")
        if self.organization:
            qs = qs.filter(organization=self.organization)
        block_title = to_str(data.get("block"))
        if block_title:
            block_title = f"{self.block_prefix}{block_title}"
            by_block = qs.filter(home_number=home_number, blocks__title__iexact=block_title)

            entrance = data.get("entrance")
            if not is_blank(entrance) and by_block.count() > 1:
                by_entrance = by_block.filter(entrance=int(float(entrance)))
                if by_entrance.exists():
                    by_block = by_entrance

            found = by_block.count()
            if found > 1:
                raise SkipRow(
                    f"blok='{block_title}', xonadon={home_number} bo`yicha {found} ta uy topildi{self.org_hint} — "
                    "noaniq, --org bilan cheklang"
                )
            if found == 1:
                return by_block.first()
            if self.strict_block:
                raise SkipRow(f"blok='{block_title}', xonadon={home_number} topilmadi{self.org_hint}")
            self.stdout.write(
                self.style.WARNING(
                    f"  [{row_num}] blok='{block_title}' bo`yicha topilmadi, raqam bo`yicha qidirilmoqda"
                )
            )

        matches = qs.filter(home_number=home_number)
        if matches.count() > 1:
            raise SkipRow(f"xonadon={home_number} bir nechta uyga mos keldi ({matches.count()} ta), blokni aniqlang")
        home = matches.first()
        if not home:
            raise SkipRow(f"xonadon={home_number}, blok={block_title} topilmadi{self.org_hint}")
        return home

    @property
    def org_hint(self):
        return f' ("{self.organization.name}" org ichida)' if self.organization else ""

    def _org_id_for(self, home):
        return home.organization_id or (self.organization.pk if self.organization else None)

    def _home_label(self, home):
        block = home.blocks
        project = block.projects.title if block and block.projects_id else "-"
        return (
            f"home_id={home.id} blok='{block.title if block else '-'}' (project='{project}') "
            f"xonadon={home.home_number} kirish={home.entrance} qavat={home.floor.number if home.floor_id else '-'}"
        )

    def _resolve_user(self, data, row_num):
        name = to_str(data.get("locked_by"))
        if not name:
            return None
        user = User.objects.filter(full_name__iexact=name).first()
        if not user:
            parts = name.split()
            if len(parts) >= 2:
                user = User.objects.filter(full_name__iexact=" ".join(reversed(parts))).first()
        if not user:
            self.stdout.write(self.style.WARNING(f'  [{row_num}] user topilmadi: "{name}"'))
        return user

    def _get_or_create_client(self, data, home, row_num):
        full_name = to_str(data.get("client_full_name"))
        if not full_name:
            raise SkipRow("mijoz F.I.Sh yo`q")

        values = {
            "phone_number": fmt_phone(data.get("phone_number")),
            "phone_number2": fmt_phone(data.get("phone_number2")),
            "passport": (to_str(data.get("passport")) or "")[:20],
            "passport_date": parse_date(data.get("passport_date")),
            "address": (to_str(data.get("address")) or "")[:500],
            "from_who": to_str(data.get("from_who")),
            "organization_id": self._org_id_for(home),
        }

        candidates = Client.objects.filter(full_name__iexact=full_name)
        if values["organization_id"]:
            candidates = candidates.filter(organization_id=values["organization_id"])

        client = candidates.first()
        if client:
            changed = self._fill(client, values, skip_defaults={"phone_number": PLACEHOLDER_PHONE})
            if changed:
                self.stdout.write(f"  [{row_num}] mijoz yangilandi: {client.full_name} -> {', '.join(changed)}")
            return client

        client = Client(full_name=full_name, **dict(values, phone_number=values["phone_number"] or PLACEHOLDER_PHONE))
        client.save()
        self.stats["clients_created"] += 1
        self.stdout.write(f"  [{row_num}] mijoz yaratildi: {full_name}")
        return client

    def _fill(self, instance, values, skip_defaults=None):
        skip_defaults = skip_defaults or {}
        changed = []
        for field, value in values.items():
            if value in (None, ""):
                continue
            current = getattr(instance, field)
            is_empty = current in (None, "") or current == skip_defaults.get(field)
            if (is_empty or self.overwrite) and differs(current, value):
                setattr(instance, field, value)
                changed.append(field)
        if changed:
            instance.save(update_fields=changed)
        return changed

    @transaction.atomic
    def _apply_row(self, data, company, row_num):
        home = self._find_home(data, row_num)

        raw_status = to_str(data.get("home_status")) or ""
        new_status = STATUS_MAP.get(norm_header(raw_status))
        if not new_status:
            raise SkipRow(f'noma`lum status: "{raw_status}"')

        if new_status == Home.HomeStatus.AVAILABLE:
            raise SkipRow(f"status '{raw_status}' — bo`sh uy, o`tkazib yuborildi")

        client = self._get_or_create_client(data, home, row_num)
        user = self._resolve_user(data, row_num)

        booking_values = {
            "booking_no": to_str(data.get("booking_no")),
            "map_key": to_str(data.get("map_key")),
            "description": to_str(data.get("description")),
            "deadline": parse_date(data.get("deadline")),
            "price_per_m2": to_decimal(data.get("price_per_m2")),
            "contract_price": to_decimal(data.get("total_price")),
            "manual_down_payment": to_decimal(data.get("down_payment")),
        }

        contract_date = parse_date(data.get("contract_date"))
        created_at = None
        if contract_date:
            created_at = timezone.make_aware(datetime.combine(contract_date, time(12, 0)))

        existing = (
            Booking.objects.select_related("client")
            .filter(home=home, status=Booking.BookingStatus.ACTIVE)
            .order_by("-created_at")
            .first()
        )

        if existing:
            if existing.client_id != client.id:
                self.stats["conflicts"] += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"  [{row_num}] KONFLIKT: {self._home_label(home)} da allaqachon boshqa mijozning "
                        f"aktiv bookingi bor\n"
                        f'      bazada:  #{existing.id} "{existing.client.full_name}" '
                        f"shartnoma={existing.booking_no} map_key={existing.map_key} "
                        f"sana={existing.created_at:%Y-%m-%d}\n"
                        f'      excelda: "{client.full_name}" shartnoma={booking_values["booking_no"]} '
                        f"map_key={booking_values['map_key']} (excel: bino={to_str(data.get('block'))} "
                        f"pod'ezd={to_str(data.get('entrance'))} qavat={to_str(data.get('floor'))})"
                    )
                )
                if not self.replace_client:
                    raise SkipRow("konflikt — qator o`tkazib yuborildi (--replace-client bilan majburlash mumkin)")

                existing.client = client
                existing.save(update_fields=["client"])
                self.stdout.write(self.style.WARNING(f"  [{row_num}] booking #{existing.id} mijozi almashtirildi"))

            values = dict(booking_values, company_id=company.id, organization_id=self._org_id_for(home))
            if created_at:
                values["created_at"] = created_at
            changed = self._fill(existing, values)
            if changed:
                self.stats["updated"] += 1
                self.stdout.write(f"  [{row_num}] booking yangilandi #{existing.id}: {', '.join(changed)}")
            booking_client = existing.client
        else:
            booking = Booking(
                home=home,
                client=client,
                company=company,
                organization_id=self._org_id_for(home),
                **booking_values,
            )
            if created_at:
                booking.created_at = created_at
            booking.save()
            self.stats["created"] += 1
            booking_client = client
            missing_money = [f for f in BOOKING_MONEY_FIELDS if not booking_values.get(f)]
            note = f" (narx yo`q: {', '.join(missing_money)})" if missing_money else ""
            self.stdout.write(
                f"  [{row_num}] booking yaratildi: xonadon={home.home_number} "
                f"kirish={home.entrance} | {client.full_name} | {raw_status}{note}"
            )

        if home.home_status != new_status:
            old_status = home.home_status
            HomeService.change_status(home_id=home.id, new_status=new_status, user=user, client=booking_client)
            self.stats["status_changed"] += 1
            self.stdout.write(f"  [{row_num}] status: {old_status} -> {new_status}")
