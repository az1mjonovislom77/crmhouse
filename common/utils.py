import re
from datetime import datetime, time, timedelta

from django.db.models import Q
from django.utils import timezone


def normalize_phone(phone: str) -> str:
    if not phone:
        return ''
    digits = re.sub(r'\D', '', phone)
    return digits[-9:] if len(digits) >= 9 else digits


def local_day_start(day):
    return timezone.make_aware(datetime.combine(day, time.min))


def date_range_q(field, date_from=None, date_to=None):
    """Inclusive local-date range as sargable __gte/__lt lookups (keeps datetime indexes usable)."""
    q = Q()
    if date_from:
        q &= Q(**{f'{field}__gte': local_day_start(date_from)})
    if date_to:
        q &= Q(**{f'{field}__lt': local_day_start(date_to + timedelta(days=1))})
    return q


def apply_date_range(qs, field, date_from=None, date_to=None):
    q = date_range_q(field, date_from, date_to)
    return qs.filter(q) if q else qs
