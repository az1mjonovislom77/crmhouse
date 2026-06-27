from django.db.models import Q, Prefetch
from leads.models import Lead, LeadEvent


def get_lead_list_queryset():
    return Lead.objects.select_related('owner')


def get_lead_detail_queryset():
    return Lead.objects.select_related('owner').prefetch_related(
        Prefetch('events', queryset=LeadEvent.objects.select_related('by').order_by('at')))


def filter_leads(queryset, params):
    board = params.get('board')
    status = params.get('status')
    owner = params.get('owner')
    source = params.get('source')
    search = params.get('search')

    if board:
        queryset = queryset.filter(board=board)
    if status:
        queryset = queryset.filter(status=status)
    if owner:
        queryset = queryset.filter(owner_id=owner)
    if source:
        queryset = queryset.filter(source=source)
    if search:
        queryset = queryset.filter(
            Q(full_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search))
    return queryset
