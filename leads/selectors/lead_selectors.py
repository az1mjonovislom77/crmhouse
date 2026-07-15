from django.db.models import Count, Prefetch, Q
from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError

from common.utils import apply_date_range
from leads.models import Lead, LeadEvent
from leads.permissions import is_lead_admin

LEAD_ORDERING_FIELDS = {'last_contacted', '-last_contacted', 'created_at', '-created_at'}


def get_lead_list_queryset():
    return Lead.objects.select_related('owner', 'assignee')


def get_lead_detail_queryset():
    return Lead.objects.select_related('owner', 'assignee').prefetch_related(
        Prefetch('events', queryset=LeadEvent.objects.select_related('by').order_by('at')))


def scope_leads_for_user(queryset, user):
    if is_lead_admin(user):
        return queryset
    return queryset.filter(Q(owner_id=user.id) | Q(assignee_id=user.id))


def get_status_counts(queryset, user=None):
    rows = queryset.values('status').annotate(n=Count('id'))
    counts = {r['status']: r['n'] for r in rows}
    if user and not is_lead_admin(user):
        counts['topshiriqlar'] = queryset.filter(
            status='topshiriqlar', assignee_id=user.id).count()
    counts['all'] = sum(counts.values())
    return counts


def filter_leads(queryset, params, user=None):
    board = params.get('board')
    status = params.get('status')
    owner = params.get('owner')
    assignee = params.get('assignee')
    source = params.get('source')
    search = params.get('search')
    last_contacted_from = params.get('last_contacted_from')
    last_contacted_to = params.get('last_contacted_to')
    ordering = params.get('ordering')

    if board:
        queryset = queryset.filter(board=board)
    if status:
        if status == 'topshiriqlar' and user and not is_lead_admin(user):
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

    if last_contacted_from or last_contacted_to:
        date_from = parse_date(last_contacted_from) if last_contacted_from else None
        date_to = parse_date(last_contacted_to) if last_contacted_to else None
        if last_contacted_from and date_from is None:
            raise ValidationError({
                'last_contacted_from': "Noto'g'ri sana formati, YYYY-MM-DD bo'lishi kerak",
            })
        if last_contacted_to and date_to is None:
            raise ValidationError({
                'last_contacted_to': "Noto'g'ri sana formati, YYYY-MM-DD bo'lishi kerak",
            })
        queryset = apply_date_range(queryset, 'last_contacted', date_from, date_to)

    if ordering:
        if ordering not in LEAD_ORDERING_FIELDS:
            raise ValidationError({
                'ordering': f"Ruxsat etilgan qiymatlar: {', '.join(sorted(LEAD_ORDERING_FIELDS))}",
            })
        queryset = queryset.order_by(ordering, '-id')

    return queryset
