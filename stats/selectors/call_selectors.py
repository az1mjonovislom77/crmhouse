from contact_center.models import CallRecord


def get_total_calls(date_from=None, date_to=None):
    qs = CallRecord.objects.all()

    if date_from:
        qs = qs.filter(calldate__date__gte=date_from)
    if date_to:
        qs = qs.filter(calldate__date__lte=date_to)
    return qs
