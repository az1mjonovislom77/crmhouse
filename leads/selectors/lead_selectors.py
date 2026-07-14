from django.db.models import Q, Prefetch, Count
from leads.models import Lead, LeadEvent


def get_lead_list_queryset():
    return Lead.objects.select_related('owner', 'assignee')


def get_lead_detail_queryset():
    return Lead.objects.select_related('owner', 'assignee').prefetch_related(
        Prefetch('events', queryset=LeadEvent.objects.select_related('by').order_by('at')))


def get_status_counts(queryset, user=None):
    rows = queryset.values('status').annotate(n=Count('id'))
    counts = {r['status']: r['n'] for r in rows}
    if user and not user.is_staff:
        counts['topshiriqlar'] = queryset.filter(
            status='topshiriqlar', assignee_id=user.id,
        ).count()
    counts['all'] = sum(counts.values())
    return counts


def filter_leads(queryset, params, user=None):
    board = params.get('board')
    status = params.get('status')
    owner = params.get('owner')
    assignee = params.get('assignee')
    source = params.get('source')
    search = params.get('search')

    if board:
        queryset = queryset.filter(board=board)
    if status:
        if status == 'topshiriqlar' and user and not user.is_staff:
            queryset = queryset.filter(status='topshiriqlar', assignee_id=user.id)
        else:
            queryset = queryset.filter(status=status)
    if owner:
        queryset = queryset.filter(owner_id=owner)
    if assignee:
        queryset = queryset.filter(assignee_id=assignee)
    if source:
        queryset = queryset.filter(source=source)
    if search:
        queryset = queryset.filter(
            Q(full_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search))
    return queryset
