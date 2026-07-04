from home.models import Home, HomeStatusHistory

SOLD_STATUSES = [
    Home.HomeStatus.SOLD,
    Home.HomeStatus.KALIT_TOPSHIRILDI,
    Home.HomeStatus.NOMIGA_OTKAZIB_BERILDI,
]


def get_sold_events(date_from=None, date_to=None):
    qs = HomeStatusHistory.objects.filter(to_status__in=SOLD_STATUSES).exclude(from_status__in=SOLD_STATUSES)
    if date_from:
        qs = qs.filter(changed_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(changed_at__date__lte=date_to)
    return qs
