from leads.models import Lead

SUCCESS_STATUS = "muvaffaqiyatli"


def get_total_success_leads(date_from=None, date_to=None):
    qs = Lead.objects.filter(board=Lead.BOARD_SALES, status=SUCCESS_STATUS)

    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
    return qs


def get_total_meetings(date_from=None, date_to=None):
    qs = Lead.objects.filter(meeting_at__isnull=False)

    if date_from:
        qs = qs.filter(meeting_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(meeting_at__date__lte=date_to)
    return qs

