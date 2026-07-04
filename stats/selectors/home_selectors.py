from datetime import date
from decimal import Decimal
from django.db.models import Count, ExpressionWrapper, Q
from django.db.models.functions import TruncMonth
from common.utils import apply_date_range, last_months, local_day_start, to_millions, MONTH_LABELS_UZ
from home.models import Home, HomeStatusHistory
from stats.selectors.booking_selectors import CONTRACT_PRICE, MONEY

SOLD_STATUSES = [
    Home.HomeStatus.SOLD,
    Home.HomeStatus.KALIT_TOPSHIRILDI,
    Home.HomeStatus.NOMIGA_OTKAZIB_BERILDI,
]


def get_sold_events(date_from=None, date_to=None):
    qs = HomeStatusHistory.objects.filter(to_status__in=SOLD_STATUSES).exclude(from_status__in=SOLD_STATUSES)
    return apply_date_range(qs, 'changed_at', date_from, date_to)


def get_homes():
    return Home.objects.all()


def get_home_status_counts(qs):
    counts = dict(qs.order_by().values_list('home_status').annotate(total=Count('id')))
    return {status: counts.get(status, 0) for status in Home.HomeStatus.values}


def get_monthly_sales(qs, months=8):
    window = last_months(months)
    window_start = local_day_start(date(window[0][0], window[0][1], 1))

    rows = (
        qs.filter(changed_at__gte=window_start)
        .annotate(month=TruncMonth('changed_at'))
        .values('month')
        .annotate(sold=Count('home', distinct=True))
    )
    counts = {(r['month'].year, r['month'].month): r['sold'] for r in rows}
    return [{'month': MONTH_LABELS_UZ[month - 1], 'sold': counts.get((year, month), 0)} for year, month in window]


def get_top_sellers(qs, limit=5):
    rows = (
        qs.filter(changed_by__isnull=False)
        .order_by()
        .annotate(price=ExpressionWrapper(CONTRACT_PRICE, output_field=MONEY))
        .values('changed_by', 'changed_by__full_name', 'home', 'price')
        .distinct()
    )
    sellers = {}
    for row in rows:
        seller = sellers.setdefault(
            row['changed_by'], {'name': row['changed_by__full_name'], 'sold': 0, 'revenue': Decimal(0)},
        )
        seller['sold'] += 1
        seller['revenue'] += row['price'] or 0
    top = sorted(sellers.values(), key=lambda s: (-s['sold'], -s['revenue']))[:limit]
    return [{'name': s['name'], 'sold': s['sold'], 'revenue': to_millions(s['revenue'])} for s in top]


def get_block_occupancy(qs):
    rows = (
        qs.filter(blocks__isnull=False)
        .order_by()
        .values('blocks_id', 'blocks__title')
        .annotate(total=Count('id'),
                  occupied=Count('id', filter=~Q(home_status=Home.HomeStatus.AVAILABLE)))
        .order_by('blocks__title')
    )
    return [{'block': r['blocks__title'], 'total': r['total'], 'occupied': r['occupied']} for r in rows]
