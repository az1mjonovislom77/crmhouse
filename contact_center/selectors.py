from django.db.models import Q


def scope_call_records(queryset, request):
    if request.user.is_staff:
        return queryset
    org = getattr(request.user, 'organization', None)
    if org is None:
        return queryset.none()
    return queryset.filter(Q(user__isnull=True) | Q(user__organization=org))
