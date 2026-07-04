from django.db.models import Count, Q

from common.utils import date_range_q
from leads.models import Lead, STATUS_NEW, STATUS_SUCCESS


def get_leads():
    return Lead.objects.all()


def get_lead_stats(qs, date_from=None, date_to=None):
    """One aggregate query returning total/new/success lead counts and meetings."""
    created_range = date_range_q('created_at', date_from, date_to)
    meeting_range = date_range_q('meeting_at', date_from, date_to)

    return qs.aggregate(
        total=Count('id', filter=created_range or None),
        new=Count('id', filter=(created_range & Q(board=Lead.BOARD_SALES, status=STATUS_NEW)) or None),
        success=Count('id', filter=(created_range & Q(board=Lead.BOARD_SALES, status=STATUS_SUCCESS)) or None),
        meetings=Count('id', filter=(meeting_range & Q(meeting_at__isnull=False)) or None),
    )
