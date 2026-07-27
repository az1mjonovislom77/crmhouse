from common.utils import apply_date_range
from contact_center.models import CallRecord


def get_total_calls(date_from=None, date_to=None):
    return apply_date_range(CallRecord.objects.all(), "calldate", date_from, date_to)
