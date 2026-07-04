from common.utils import apply_date_range
from home.models import Home, HomeStatusHistory

SOLD_STATUSES = [
    Home.HomeStatus.SOLD,
    Home.HomeStatus.KALIT_TOPSHIRILDI,
    Home.HomeStatus.NOMIGA_OTKAZIB_BERILDI,
]


def get_sold_events(date_from=None, date_to=None):
    qs = HomeStatusHistory.objects.filter(to_status__in=SOLD_STATUSES).exclude(from_status__in=SOLD_STATUSES)
    return apply_date_range(qs, 'changed_at', date_from, date_to)
