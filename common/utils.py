import re
from datetime import datetime, time, timedelta

from django.db.models import Q
from django.utils import timezone

MONTH_LABELS_UZ = ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'Iyun', 'Iyul', 'Avg', 'Sen', 'Okt', 'Noy', 'Dek']


def normalize_phone(phone: str) -> str:
    if not phone:
        return ''
    digits = re.sub(r'\D', '', phone)
    return digits[-9:] if len(digits) >= 9 else digits


def local_day_start(day):
    return timezone.make_aware(datetime.combine(day, time.min))


def date_range_q(field, date_from=None, date_to=None):
    q = Q()
    if date_from:
        q &= Q(**{f'{field}__gte': local_day_start(date_from)})
    if date_to:
        q &= Q(**{f'{field}__lt': local_day_start(date_to + timedelta(days=1))})
    return q


def apply_date_range(qs, field, date_from=None, date_to=None):
    q = date_range_q(field, date_from, date_to)
    return qs.filter(q) if q else qs


def last_months(months):
    today = timezone.localdate()
    last_index = today.year * 12 + today.month - 1
    window = []
    for index in range(last_index - months + 1, last_index + 1):
        year, month = divmod(index, 12)
        window.append((year, month + 1))
    return window


def to_millions(value):
    return round(float(value or 0) / 1_000_000, 1)
