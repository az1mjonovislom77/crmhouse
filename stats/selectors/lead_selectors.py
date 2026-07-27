from django.db.models import Count, Q

from common.utils import apply_date_range, date_range_q
from leads.models import STATUS_NEW, STATUS_SUCCESS, Lead, LeadEvent

FUNNEL_STAGES = [
    (STATUS_NEW, "Yangi murojaat"),
    ("uchrashuv", "Uchrashuv"),
    ("jarayon", "Jarayon"),
    (STATUS_SUCCESS, "Muvaffaqiyatli"),
]


def get_leads():
    return Lead.objects.filter(board=Lead.BOARD_SALES)


def get_lead_stats(qs, date_from=None, date_to=None):
    created_range = date_range_q("created_at", date_from, date_to)
    meeting_range = date_range_q("meeting_at", date_from, date_to)

    return qs.aggregate(
        total=Count("id", filter=created_range or None),
        new=Count("id", filter=(created_range & Q(status=STATUS_NEW)) or None),
        meetings=Count("id", filter=(meeting_range & Q(meeting_at__isnull=False)) or None),
    )


def get_success_conversions(qs, date_from=None, date_to=None):
    events = LeadEvent.objects.filter(
        type=LeadEvent.TYPE_STATUS,
        to_value=STATUS_SUCCESS,
        lead__in=qs,
    ).exclude(from_value=STATUS_SUCCESS)
    converted = apply_date_range(events, "at", date_from, date_to).values("lead").distinct().count()

    legacy = qs.filter(status=STATUS_SUCCESS).exclude(
        events__type=LeadEvent.TYPE_STATUS,
        events__to_value=STATUS_SUCCESS,
    )
    legacy_count = apply_date_range(legacy, "created_at", date_from, date_to).count()

    return converted + legacy_count


def get_lead_funnel(qs, date_from=None, date_to=None):
    qs = apply_date_range(qs, "created_at", date_from, date_to)
    counts = dict(qs.order_by().values_list("status").annotate(total=Count("id")))
    return [{"stage": label, "count": counts.get(status, 0)} for status, label in FUNNEL_STAGES]


def get_lead_sources(qs, date_from=None, date_to=None):
    qs = apply_date_range(qs, "created_at", date_from, date_to)
    rows = qs.order_by().values("source").annotate(value=Count("id")).order_by("-value")
    return [{"name": r["source"], "value": r["value"]} for r in rows]
